#!/usr/bin/python3 -u

import fileinput, os, shutil

'''repair_torrc() function will be called when we want to gurantee the existence of:
1. /etc/torrc.d/95_whonix.conf
2. /etc/tor/torrc
3. "%include /etc/torrc.d/95_whonix.conf" line in /etc/tor/torrc file
'''

if os.path.exists('/usr/share/anon-gw-base-files/gateway'):
    whonix=True
else:
    whonix=False

def repair_torrc():
    repair_torrc_d()

    if not os.path.exists('/etc/tor/torrc'):
        with open('/etc/tor/torrc', "w+") as f:
            f.write("%include /etc/torrc.d/95_whonix.conf")
            f.write('\n')
    else:
        with open('/etc/tor/torrc', "r") as f:
            lines = f.readlines()
            f.close()

        torrcd_line_exists = False
        for line in lines:
            str = line.strip()
            if (str == '%include /etc/torrc.d/95_whonix.conf'):
                torrcd_line_exists = True

        if not torrcd_line_exists:
            with open('/etc/tor/torrc', "a") as f:
                f.write("%include /etc/torrc.d/95_whonix.conf\n")
                f.write('\n')


'''repair_torrc_d() will gurantee the existence of /etc/torrc.d/95_whonix.conf
and if anon-connection-wizard is in Whonix,
then also gurantee the existence of /usr/local/etc/torrc.d/95_whonix.conf
'''
def repair_torrc_d():
    if not os.path.exists('/etc/torrc.d/95_whonix.conf'):
        os.makedirs('/etc/torrc.d/95_whonix.conf')
    if whonix and not os.path.exists('/usr/local/etc/torrc.d/95_whonix.conf'):
        os.makedirs('/usr/local/etc/torrc.d/95_whonix.conf')
