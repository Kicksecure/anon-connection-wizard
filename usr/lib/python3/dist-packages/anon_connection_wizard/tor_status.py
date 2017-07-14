#!/usr/bin/python3 -u

import sys, fileinput
from subprocess import call
import os, time

def tor_status():
    if not os.path.exists('/etc/tor/torrc'):
        return 'no_torrc'

    fh = open('/etc/tor/torrc','r')
    lines = fh.readlines()
    fh.close()

    line_exists = False
    for line in lines:
        if line.strip() == '#DisableNetwork 0':
            line_exists = True
            return 'tor_disabled'
        elif line.strip() == 'DisableNetwork 0':
            line_exists = True

    if not line_exists:
        return 'bad_torrc'

'''Unlike tor_status() function which only shows the current state of the /etc/tor/torrc,
set_enabled() and set_disabled() function will repair the missing torrc or DisableNetwork line.
This makes sense because when we call set_enabled() or set_disabled() we really want Tor work,
rather than receive a 'no_torrc' or 'bad_torrc' complain, which is not helpful for users.\
'''
def set_enabled():
    _repair_torrc()  # This gurantees a good torrc

    fh = open('/etc/tor/torrc','r')
    lines = fh.readlines()
    fh.close()

    for line in lines:
        if line.strip() == 'DisableNetwork 0':

            command = 'systemctl --no-pager restart tor@default'
            tor_status = call(command, shell=True)

            if tor_status != 0:
                return 'cannot_connect'

            command = 'systemctl --no-pager status tor@default'
            tor_status = call(command, shell=True)

            if tor_status != 0:
                return 'cannot_connect'

            return 'tor_already_enabled'

        elif line.strip() == '#DisableNetwork 0':

            for i, line in enumerate(fileinput.input('/etc/tor/torrc', inplace=1)):
                sys.stdout.write(line.replace('#DisableNetwork 0', 'DisableNetwork 0'))

            command = 'systemctl --no-pager restart tor@default'
            tor_status = call(command, shell=True)

            if tor_status != 0:
                return 'cannot_connect'

            command = 'systemctl --no-pager status tor@default'
            tor_status = call(command, shell=True)

            if tor_status != 0:
                return 'cannot_connect'

            return 'tor_enabled'

    return 'Unexpected result'

def set_disabled():
    _repair_torrc()  # This gurantees a good torrc
    
    fh = open('/etc/tor/torrc','r')
    lines = fh.readlines()
    fh.close()

    for line in lines:
        if line.strip() == '#DisableNetwork 0':
            return 'tor_already_disabled'

        elif line.strip() == 'DisableNetwork 0':
            for i, line in enumerate(fileinput.input('/etc/tor/torrc', inplace=1)):
                sys.stdout.write(line.replace('DisableNetwork 0', '#DisableNetwork 0'))

            command = 'systemctl --no-pager stop tor@default'
            call(command, shell=True)

            return 'tor_disabled'

'''_repair_torrc() function will be called when we want to gurantee there will be 
a /etc/tor/torrc file with a "#DisableNetwork 0" or "DisableNetwork 0" line.

It will return:
'fixed_nothing' if everything is good in torrc
'fixed_missing_torrc' and 'fixed_missing_disable_line'

TODO: if "%include /etc/torrc.d\n" line is decided in to add into /etc/tor/torrc in the future,
we should also try to repair it if it is missing.
'''
def _repair_torrc():
    if not os.path.exists('/etc/tor/torrc'):
    ## When /etc/tor/torrc is missing, Tor should work not very well, which means Tor is disabled.
    ## Therefore, we can safely append "#DisableNetwork 0", rather than "DisableNetwork 0".
    ## We intended to wirte three parts of the text separately so that 
    ## each of them will be easier to find in the future.

        with open('/etc/tor/torrc', "a") as f:
            f.write("# This file is part of Whonix\n\
# Copyright (C) 2012 - 2013 adrelanos <adrelanos at riseup dot net>\n\
# See the file COPYING for copying conditions.\n\
\n\
# Use this file for your user customizations.\n\
# Please see /etc/tor/torrc.examples for help, options, comments etc.\n\
\n\
# Anything here will override Whonix's own Tor config customizations in\n\
# /usr/share/tor/tor-service-defaults-torrc\n\
\n\
# Enable Tor through anon-connection-wizard or manually uncomment \"DisableNetwork 0\" by\n\
# removing the # in front of it.\n")
            #f.write("%include /etc/torrc.d\n")  # TODO: uncomment this when needed 
            f.write("#DisableNetwork 0\n")
        return 'fixed_missing_torrc'
    else:
        fh = open('/etc/tor/torrc','r')
        lines = fh.readlines()
        fh.close()

        for line in lines:
            if (line.strip() == '#DisableNetwork 0') or (line.strip() == 'DisableNetwork 0'):
                return 'fixed_nothing'

        ## Notice that from now on, '#DisableNetwork 0' or 'DisableNetwork 0' must not be in torrc
        ## So we need to append it
        with open('/etc/tor/torrc', "a") as f:
            #f.write("\n%include /etc/torrc.d\n")  # TODO: uncomment this when needed 
            f.write("\n#DisableNetwork 0\n")  # it is important to prefix a \n in case torrc does not contain \n at file end
        return 'fixed_missing_disable_line'
            

                

