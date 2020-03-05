#!/usr/bin/python3 -u

## Copyright (C) 2018 - 2019 ENCRYPTED SUPPORT LP <adrelanos@riseup.net>
## See the file COPYING for copying conditions.

import fileinput, os, shutil

'''repair_torrc() function will be called when we want to guarantee the existence of:
1. "%include /etc/torrc.d/95_whonix.conf" line in /etc/tor/torrc file
2. "%include /usr/local/etc/torrc.d/" line in /etc/torrc.d/95_whonix.conf file
'''

if os.path.exists('/usr/share/anon-gw-base-files/gateway'):
    whonix=True
else:
    whonix=False

def repair_torrc():
    if not os.path.exists('/etc/torrc.d/'):
        os.makedirs('/etc/torrc.d/')

    if whonix and not os.path.exists('/usr/local/etc/torrc.d/'):
        os.makedirs('/usr/local/etc/torrc.d/')

    if not os.path.exists('/etc/torrc.d/95_whonix.conf'):
        with open('/etc/torrc.d/95_whonix.conf', "w+") as f:
            f.write("%include /usr/local/etc/torrc.d/")
            f.write('\n')

    if not os.path.exists('/etc/tor/torrc'):
        with open('/etc/tor/torrc', "w+") as f:
            f.write("%include /etc/torrc.d/")
            f.write('\n')
    else:
        with open('/etc/tor/torrc', "r") as f:
            lines = f.readlines()
            f.close()

        torrcd_line_exists = False
        for line in lines:
            str = line.strip()
            if (str == '%include /etc/torrc.d/'):
                torrcd_line_exists = True

        if not torrcd_line_exists:
            with open('/etc/tor/torrc', "a") as f:
                f.write("%include /etc/torrc.d/")
                f.write('\n')
