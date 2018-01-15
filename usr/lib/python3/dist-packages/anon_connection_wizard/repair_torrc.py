#!/usr/bin/python3 -u

import fileinput, os, shutil


'''repair_torrc() function will be called when we want to gurantee the existence of:
1. /etc/tor/torrc file
'''

def repair_torrc():
    repair_torrc_d()


'''repair_torrc_d() will gurantee the existence of /etc/torrc.d and /usr/local/etc/torrc.d/
'''
def repair_torrc_d():
    if not os.path.exists('/etc/torrc.d/'):
        os.makedirs('/etc/torrc.d/')
    if not os.path.exists('/usr/local/etc/torrc.d/'):
        os.makedirs('/usr/local/etc/torrc.d/')
