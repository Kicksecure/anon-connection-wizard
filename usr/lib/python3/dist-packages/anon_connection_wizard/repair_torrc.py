#!/usr/bin/python3 -su

## Copyright (C) 2018 - 2025 ENCRYPTED SUPPORT LLC <adrelanos@whonix.org>
## See the file COPYING for copying conditions.

import os, sys
import subprocess

if os.path.exists('/usr/share/anon-gw-base-files/gateway'):
    whonix = True
else:
    whonix = False

def repair_torrc():
    if not whonix:
        ## Not implemented for non-Whonix yet.
        return

    try:
        command = ['leaprun', 'tor-config-sane']
        p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        if not p.returncode == 0:
            print("ERROR: leaprun tor-config-sane Exit Code:", p.returncode)
    except Exception as e:
        error_msg = "tor-config-sane unexpected error: " + str(e)
        print(error_msg)

def main():
    repair_torrc()

if __name__ == "__main__":
    main()
