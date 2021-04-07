#!/usr/bin/python3 -u

## Copyright (C) 2021 - 2021 ENCRYPTED SUPPORT LP <adrelanos@whonix.org>
## See the file COPYING for copying conditions.

import os, sys
from subprocess import check_output, STDOUT, call, Popen, PIPE

if os.path.exists('/usr/share/anon-gw-base-files/gateway'):
    whonix=True
else:
    whonix=False

def edit_etc_resolv_conf():
   if not whonix:
      ## Not implemented for non-Whonix.
      return

   try:
      command = ['/usr/lib/anon-gw-anonymizer-config/edit-etc-resolv-conf']
      p = Popen(command, stdout=PIPE, stderr=PIPE)
      stdout, stderr = p.communicate()
   except:
      error_msg = "edit-etc-resolv-conf unexpected error: " + str(sys.exc_info()[0])
      print(error_msg)

def main():
   edit_etc_resolv_conf()

if __name__ == "__main__":
    main()
