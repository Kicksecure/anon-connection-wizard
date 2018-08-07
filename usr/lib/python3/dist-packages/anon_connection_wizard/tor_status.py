#!/usr/bin/python3 -u

import sys, fileinput
import os, time
from subprocess import call
from anon_connection_wizard import repair_torrc

if os.path.exists('/usr/share/anon-gw-base-files/gateway'):
    whonix=True
else:
    whonix=False

if whonix:
    DisableNetwork_torrc_path = '/usr/local/etc/torrc.d/40_tor_control_panel.conf'
else:
    DisableNetwork_torrc_path = '/etc/torrc.d/40_tor_control_panel.conf'

def tor_status():
    # Known issue:
    # before torrc.d get used, both 40_tor_control_panel.conf and 50_user.conf
    # are explicitly used in 95_whonix.conf. Therefore, when 50_user.conf is missing,
    # Tor will fail to start. This probelm can be solved by rebooting or doing
    # systemctl restart anon-gw-anonymizer-config.service , which runs
    # ExecStart=/usr/lib/anon-gw-anonymizer-config/make-sure-torrc-exist
    if not os.path.exists(DisableNetwork_torrc_path):
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
        return 'missing_disablenetwork_line'
    else:
        if tor_disabled:
            return "tor_disabled"
        else:
            return 'tor_enabled'

'''Unlike tor_status() function which only shows the current state of the anon_connection_wizard.conf,
set_enabled() and set_disabled() function will try to repair the missing torrc or DisableNetwork line.
This makes sense because when we call set_enabled() or set_disabled() we really want Tor to work,
rather than receive a 'no_torrc' or 'missing_disablenetwork_line' complain, which is not helpful for users.

set_enabled() will return a turple with two value: a string of error type and an int of error code.
'''

'''set_enabled() is specified as follows:
set_enabled() will:
1. gurantee the existence of 40_tor_control_panel.conf
2. gurantee the final value of DisableNetwork is 0 in the file
3. gurantee Tor uses DisableNetwork 0
'''
def set_enabled():
    ## change DisableNetwork line according to tor_status
    status = tor_status()
    if status == "no_torrc":
        with open(DisableNetwork_torrc_path,'w+') as f:
            f.write('DisableNetwork 0')
            f.write('\n')
    elif status == "tor_disabled":
        for i, line in enumerate(fileinput.input(DisableNetwork_torrc_path, inplace=1)):
            sys.stdout.write(line.replace('DisableNetwork 1', 'DisableNetwork 0'))
    elif status == "tor_enabled":
        # do nothing
        pass
    elif status == "missing_disablenetwork_line":
        with open(DisableNetwork_torrc_path,'a') as f:
            f.write('DisableNetwork 0')
            f.write('\n')

    ## start the Tor now
    command = 'systemctl --no-pager restart tor@default'
    tor_status_code = call(command, shell=True)

    if tor_status_code != 0:
        return 'cannot_connect', tor_status_code

    ## we have to reload to open /var/run/tor/control and create /var/run/tor/control.authcookie
    command = 'systemctl reload tor@default.service'
    tor_status_code = call(command, shell=True)

    command = 'systemctl --no-pager status tor@default'
    tor_status_code= call(command, shell=True)

    if tor_status_code != 0:
        return 'cannot_connect', tor_status_code

    return 'tor_enabled', tor_status_code

'''set_disabled() is specified as follows:
set_disabled() will:
1. gurantee the existence of 40_tor_control_panel.conf
2. gurantee the final value of DisableNetwork is 1 in the file
3. gurantee Tor uses DisableNetwork 1
'''
def set_disabled():
    ## change DisableNetwork line according to tor_status
    status = tor_status()
    if status == "no_torrc":
        with open(DisableNetwork_torrc_path,'w+') as f:
            f.write('DisableNetwork 1')
            f.write('\n')
    elif status == "tor_disabled":
        # do nothing
        pass
    elif status == "tor_enabled":
        for i, line in enumerate(fileinput.input(DisableNetwork_torrc_path, inplace=1)):
            sys.stdout.write(line.replace('DisableNetwork 0', 'DisableNetwork 1'))
    elif status == "missing_disablenetwork_line":
        with open(DisableNetwork_torrc_path,'a') as f:
            f.write('DisableNetwork 1')
            f.write('\n')

    ## stop the Tor now
    command = 'systemctl --no-pager stop tor@default'
    call(command, shell=True)

    return 'tor_disabled'
