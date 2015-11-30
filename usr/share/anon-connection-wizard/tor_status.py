#!/usr/bin/python

import sys, fileinput
from subprocess import call
import os, time


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

            command = 'service tor@default restart'
            tor_status = call(command, shell=True)

            if tor_status != 0:
                return 'cannot_connect'

            command = 'service tor@default status'
            tor_status = call(command, shell=True)

            if tor_status != 0:
                return 'cannot_connect'

            return 'tor_already_enabled'

        elif line.strip() == '#DisableNetwork 0':
            line_exists = True

            for i, line in enumerate(fileinput.input('/etc/tor/torrc', inplace=1)):
                sys.stdout.write(line.replace('#DisableNetwork 0', 'DisableNetwork 0'))

            command = 'service tor@default restart'
            tor_status = call(command, shell=True)

            if tor_status != 0:
                return 'cannot_connect'

            command = 'service tor@default status'
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

            command = 'service tor stop'
            call(command, shell=True)

            return 'tor_disabled'

    if not line_exists:
        return 'bad_torrc'
