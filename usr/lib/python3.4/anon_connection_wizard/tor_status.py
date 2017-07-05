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

def set_enabled():
    if not os.path.exists('/etc/tor/torrc'):
        return 'no_torrc'

    fh = open('/etc/tor/torrc','r')
    lines = fh.readlines()
    fh.close()

    line_exists = False

    for line in lines:
        if line.strip() == 'DisableNetwork 0':
            line_exists = True

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
            line_exists = True

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

    if not line_exists:
        return 'bad_torrc'


def set_disabled():
    if not os.path.exists('/etc/tor/torrc'):
        return 'no_torrc'

    fh = open('/etc/tor/torrc','r')
    lines = fh.readlines()
    fh.close()

    line_exists = False

    for line in lines:
        if line.strip() == '#DisableNetwork 0':
            line_exists = True
            return 'tor_already_disabled'

        elif line.strip() == 'DisableNetwork 0':
            line_exists = True

            for i, line in enumerate(fileinput.input('/etc/tor/torrc', inplace=1)):
                sys.stdout.write(line.replace('DisableNetwork 0', '#DisableNetwork 0'))

            command = 'systemctl --no-pager stop tor@default'
            call(command, shell=True)

            return 'tor_disabled'

    if not line_exists:
        return 'bad_torrc'
