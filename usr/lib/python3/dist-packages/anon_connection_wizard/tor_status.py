#!/usr/bin/python3 -u

## Copyright (C) 2018 - 2023 ENCRYPTED SUPPORT LP <adrelanos@whonix.org>
## See the file COPYING for copying conditions.

import sys, fileinput, tempfile
import os, subprocess

if os.path.exists('/usr/share/anon-gw-base-files/gateway'):
    whonix=True
else:
    whonix=False

DisableNetwork_torrc_path = '/usr/local/etc/torrc.d/40_tor_control_panel.conf'

def tor_status():
    print("tor_status was called.")

    # Known issue:
    # before torrc.d get used, both 40_tor_control_panel.conf and 50_user.conf
    # are explicitly used in 95_whonix.conf. Therefore, when 50_user.conf is missing,
    # Tor will fail to start. This problem can be solved by rebooting or doing
    # systemctl restart anon-gw-anonymizer-config.service
    # which runs
    # ExecStart=/usr/libexec/anon-gw-anonymizer-config/tor-config-sane
    if not os.path.exists(DisableNetwork_torrc_path):
        print("tor_status status: no_torrc")
        return "no_torrc"

    with open(DisableNetwork_torrc_path,'r') as f:
        lines = f.readlines()
        f.close()

    ''' Notice that just because we see "DisableNetwork 1" or "DisableNetwork 0"
    does not mean Tor is really disabled because there may be another line of "DisableNetwork".
    Therefore, we have to use a flag as follows.
    '''
    tor_disabled = True
    has_diable_network_line = False
    for line in lines:
        if line.strip() == 'DisableNetwork 0':
            tor_disabled = False
            has_diable_network_line = True
        elif line.strip() == 'DisableNetwork 1':
            tor_disabled = True
            has_diable_network_line = True

    if not has_diable_network_line:
        print("tor_status status: missing_disablenetwork_line")
        return 'missing_disablenetwork_line'
    else:
        if tor_disabled:
            print("tor_status status: tor_disabled")
            return "tor_disabled"
        else:
            print("tor_status status: tor_enabled")
            return 'tor_enabled'

'''Unlike tor_status() function which only shows the current state of the anon_connection_wizard.conf,
set_enabled() and set_disabled() function will try to repair the missing torrc or DisableNetwork line.
This makes sense because when we call set_enabled() or set_disabled() we really want Tor to work,
rather than receive a 'no_torrc' or 'missing_disablenetwork_line' complain, which is not helpful for users.

set_enabled() will return a tuple with two value: a string of error type and an int of error code.
'''

'''set_enabled() is specified as follows:
set_enabled() will:
1. guarantee the existence of 40_tor_control_panel.conf
2. guarantee the final value of DisableNetwork is 0 in the file
3. guarantee Tor uses DisableNetwork 0
'''
def set_enabled():
    print("set_enabled was called.")

    ## change DisableNetwork line according to tor_status
    status = tor_status()
    content = ""

    if status == "no_torrc":
        content = 'DisableNetwork 0\n'
    elif status == "tor_disabled":
        with open(DisableNetwork_torrc_path,'r') as f:
            content = f.read().replace('DisableNetwork 1', 'DisableNetwork 0')
    elif status == "missing_disablenetwork_line":
        with open(DisableNetwork_torrc_path,'r') as f:
            content = f.read() + '\n' + 'DisableNetwork 1' + '\n'
    elif status == "tor_enabled":
        return 'tor_enabled', 0

    write_to_temp_then_move(content)

    command = 'pkexec systemctl --no-pager restart tor@default'
    tor_status_code = subprocess.call(command, shell=True)

    if tor_status_code != 0:
        return 'cannot_connect', tor_status_code

    ## we have to reload to open /run/tor/control and create /run/tor/control.authcookie
    command = 'pkexec systemctl --no-pager reload tor@default.service'
    subprocess.call(command, shell=True)

    command = 'pkexec systemctl --no-pager status tor@default'
    tor_status_code = subprocess.call(command, shell=True)

    if tor_status_code != 0:
        return 'cannot_connect', tor_status_code

    return 'tor_enabled', tor_status_code

'''set_disabled() is specified as follows:
set_disabled() will:
1. guarantee the existence of 40_tor_control_panel.conf
2. guarantee the final value of DisableNetwork is 1 in the file
3. guarantee Tor uses DisableNetwork 1
'''
def set_disabled():
    print("set_disabled was called.")

    ## change DisableNetwork line according to tor_status
    status = tor_status()
    content = ""

    if status == "no_torrc" or status == "missing_disablenetwork_line":
        content = 'DisableNetwork 1\n'
    elif status == "tor_enabled":
        with open(DisableNetwork_torrc_path,'r') as f:
            content = f.read().replace('DisableNetwork 0', 'DisableNetwork 1')
    elif status == "tor_disabled":
        return 'tor_disabled'

    write_to_temp_then_move(content)

    command = 'pkexec systemctl --no-pager stop tor@default'
    subprocess.call(command, shell=True)

    return 'tor_disabled'

def write_to_temp_then_move(content):
    print(DisableNetwork_torrc_path)
    print("before:")
    cat(DisableNetwork_torrc_path)
    print("")

    handle, temp_file_path = tempfile.mkstemp()

    with open(temp_file_path, 'w') as temp_file:
        temp_file.write(content)

    subprocess.check_call(['pkexec', 'mv', temp_file_path, DisableNetwork_torrc_path])
    subprocess.check_call(['pkexec', 'chmod', '644', DisableNetwork_torrc_path])

    print(DisableNetwork_torrc_path)
    print("after:")
    cat(DisableNetwork_torrc_path)
    print("")

def cat(filename):
    if not os.path.exists(filename):
        print("File did not exist.")
        return

    with open(filename, 'r') as file:
        for line in file:
            print(line, end='')

if __name__ == "__main__":
    # Example usage
    print("Enabling...")
    print(set_enabled())
    print("Disabling...")
    print(set_disabled())
    print("Done.")
