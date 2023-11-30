#!/usr/bin/python3 -u

## Copyright (C) 2018 - 2023 ENCRYPTED SUPPORT LP <adrelanos@whonix.org>
## See the file COPYING for copying conditions.

import sys, fileinput, tempfile
import os, subprocess

if os.path.exists('/usr/share/anon-gw-base-files/gateway'):
    whonix=True
else:
    whonix=False

## TODO: code duplication
## Should use same variable as in anon_connection_wizard.py.
torrc_file_path = '/usr/local/etc/torrc.d/40_tor_control_panel.conf'

def tor_status():
    print("tor_status was called.")

    # Known issue:
    # before torrc.d get used, both 40_tor_control_panel.conf and 50_user.conf
    # are explicitly used in 95_whonix.conf. Therefore, when 50_user.conf is missing,
    # Tor will fail to start. This problem can be solved by rebooting or doing
    # systemctl restart anon-gw-anonymizer-config.service
    # which runs
    # ExecStart=/usr/libexec/anon-gw-anonymizer-config/tor-config-sane

    output = subprocess.check_output('/usr/libexec/helper-scripts/tor_enabled_check')
    output = output.decode("UTF-8").strip()

    if output == "true":
        print("tor_status status: tor_enabled")
        return "tor_enabled"
    else:
        print("tor_status status: tor_disabled")
        return "tor_disabled"

'''Unlike tor_status() function which only shows the current state of the anon_connection_wizard.conf,
set_enabled() and set_disabled() function will try to repair the missing torrc or DisableNetwork line.
This makes sense because when we call set_enabled() or set_disabled() we really want Tor to work.

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

    content = ''

    if os.path.exists(torrc_file_path):
        with open(torrc_file_path, 'r') as f:
            content = f.readlines()

    disable_network_found = False
    for line in content:
        if 'DisableNetwork' in line:
            disable_network_found = True
            break

    if disable_network_found:
        with open(torrc_file_path,'r') as f:
            content = f.read().replace('DisableNetwork 1', 'DisableNetwork 0')
    else:
        if os.path.exists(torrc_file_path):
            with open(torrc_file_path,'r') as f:
                content = f.read() + '\n' + 'DisableNetwork 0' + '\n'
        else:
            content = 'DisableNetwork 0'

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

    content = ''

    if os.path.exists(torrc_file_path):
        with open(torrc_file_path, 'r') as f:
            content = f.readlines()

    disable_network_found = False
    for line in content:
        if 'DisableNetwork' in line:
            disable_network_found = True
            break

    if disable_network_found:
        with open(torrc_file_path,'r') as f:
            content = f.read().replace('DisableNetwork 0', 'DisableNetwork 1')
    else:
        if os.path.exists(torrc_file_path):
            with open(torrc_file_path,'r') as f:
                content = f.read() + '\n' + 'DisableNetwork 1' + '\n'
        else:
            content = 'DisableNetwork 1' + '\n'

    write_to_temp_then_move(content)

    command = 'pkexec systemctl --no-pager stop tor@default'
    subprocess.call(command, shell=True)

    return 'tor_disabled'

def write_to_temp_then_move(content):
    print(torrc_file_path)
    print("before:")
    cat(torrc_file_path)
    print("")

    handle, temp_file_path = tempfile.mkstemp()
    with open(temp_file_path, 'w') as temp_file:
        temp_file.write(content)

    command = ['pkexec', '/usr/libexec/anon-connection-wizard/acw-write-torrc', temp_file_path]
    print("tor_status.py: executing:", ' '.join(command))
    subprocess.check_call(command)

    print(torrc_file_path)
    print("after:")
    cat(torrc_file_path)
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
