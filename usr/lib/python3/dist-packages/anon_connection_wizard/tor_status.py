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
    DisableNetwork_torrc_path = '/usr/local/etc/torrc.d/50_user.torrc'
else:
    DisableNetwork_torrc_path = '/etc/torrc.d/50_user.torrc'

def tor_status():
    if not os.path.exists(DisableNetwork_torrc_path):
        return "no_torrc"

    with open(DisableNetwork_torrc_path,'r') as f:
        lines = f.readlines()
        f.close()

    ''' Notice that just because we see "#DisableNetwork 0"
    does not mean Tor is really disabled because there may be another line "DisableNetwork 0".
    Therefore, we have to use a flag as follows.
    '''
    tor_disabled = False
    for line in lines:
        if line.strip() == 'DisableNetwork 0':
            return 'tor_enabled'
        elif line.strip() == '#DisableNetwork 0':
            tor_disabled = True
    if tor_disabled:
        return "tor_disabled"
    
    return 'missing_disablenetwork_line'

'''Unlike tor_status() function which only shows the current state of the anon_connection_wizard.torrc,
set_enabled() and set_disabled() function will try to repair the missing torrc or
DisableNetwork line by calling repair_torrc module.
This makes sense because when we call set_enabled() or set_disabled() we really want Tor to work,
rather than receive a 'no_torrc' or 'missing_disablenetwork_line' complain, which is not helpful for users.
'''
def set_enabled():
    ## change DisableNetwork line according to tor_status
    status = tor_status()
    if status == "no_torrc":
        with open(DisableNetwork_torrc_path,'w+') as f:
            f.write('DisableNetwork 0')
    elif status == "tor_disabled":
        # remove # to enable Tor
        with open(DisableNetwork_torrc_path,'r') as f:
            lines = f.readlines()
            f.close()
        for line in lines:
            if line.strip() == '#DisableNetwork 0':
                for i, line in enumerate(fileinput.input(DisableNetwork_torrc_path, inplace=1)):
                    sys.stdout.write(line.replace('#DisableNetwork 0', 'DisableNetwork 0'))
    elif status == "tor_enabled":
        # do nothing
        pass
    elif status == "missing_disablenetwork_line":
        with open(DisableNetwork_torrc_path,'a') as f:
            f.write('DisableNetwork 0')

    ## start the Tor now
    command = 'systemctl --no-pager restart tor@default'
    tor_status_code = call(command, shell=True)

    if tor_status_code != 0:
        return 'cannot_connect', tor_status_code
    
    command = 'systemctl --no-pager status tor@default'
    tor_status_code= call(command, shell=True)
    
    if tor_status_code != 0:
        return 'cannot_connect', tor_status_code
    
    return 'tor_enabled', tor_status_code

def set_disabled():
    ## change DisableNetwork line according to tor_status
    status = tor_status()
    if status == "no_torrc":
        with open(DisableNetwork_torrc_path,'w+') as f:
            f.write('#DisableNetwork 0')
    elif status == "tor_disabled":
        # do nothing        
        pass
    elif status == "tor_enabled":
        # prefix # to DisableNetwork line
        with open(DisableNetwork_torrc_path,'r') as f:
            lines = f.readlines()
            f.close()
        for line in lines:
            if line.strip() == 'DisableNetwork 0':
                for i, line in enumerate(fileinput.input(DisableNetwork_torrc_path, inplace=1)):
                    sys.stdout.write(line.replace('DisableNetwork 0', '#DisableNetwork 0'))
    elif status == "missing_disablenetwork_line":
        with open(DisableNetwork_torrc_path,'a') as f:
            f.write('#DisableNetwork 0')

    ## stop the Tor now
    command = 'systemctl --no-pager stop tor@default'
    call(command, shell=True)

    return 'tor_disabled'
