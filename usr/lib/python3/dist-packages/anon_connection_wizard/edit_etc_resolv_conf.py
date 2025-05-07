#!/usr/bin/python3 -su

## Copyright (C) 2021 - 2025 ENCRYPTED SUPPORT LLC <adrelanos@whonix.org>
## See the file COPYING for copying conditions.

import os, sys
from subprocess import check_output, STDOUT, call, Popen, PIPE

if os.path.exists('/usr/share/anon-gw-base-files/gateway'):
    whonix=True
else:
    whonix=False

def edit_etc_resolv_conf_add():
   if not whonix:
      ## Not implemented for non-Whonix.
      return

   try:
      command = ['leaprun', 'anon-dns-add']
      p = Popen(command, stdout=PIPE, stderr=PIPE)
      stdout, stderr = p.communicate()
   except BaseException:
      error_msg = "edit-etc-resolv-conf add unexpected error: " + str(sys.exc_info()[0])
      print(error_msg)

def edit_etc_resolv_conf_remove():
   if not whonix:
      ## Not implemented for non-Whonix.
      return

   try:
      command = ['leaprun', 'anon-dns-remove']
      p = Popen(command, stdout=PIPE, stderr=PIPE)
      stdout, stderr = p.communicate()
   except BaseException:
      error_msg = "edit-etc-resolv-conf remove unexpected error: " + str(sys.exc_info()[0])
      print(error_msg)

def main():
   edit_etc_resolv_conf_add()

if __name__ == "__main__":
    main()
