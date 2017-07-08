#!/usr/bin/python3 -u

## Copyright (C) 2014 troubadour <trobador@riseup.net>
## Copyright (C) 2014 Patrick Schleizer <adrelanos@riseup.net>
## See the file COPYING for copying conditions.

from PyQt5 import QtGui,QtWidgets
from guimessages import translations


class gui_message(QtWidgets.QMessageBox):
    def __init__(self, file_path, section):
        super(gui_message, self).__init__()

        tr = translations._translations(file_path, section)

        self.icon = tr.section.get('icon')
        self.button = tr.section.get('button')

        if tr.section.get('position') == 'topleft':
            self.move(0,0)

        self._ = tr.gettext
        self.initUI()

    def initUI(self):
        self.setWindowIcon(QtGui.QIcon("/usr/share/icons/anon-icon-pack/whonix.ico"))

        self.setIcon(getattr(QtGui.QMessageBox, self.icon))
        self.setStandardButtons(getattr(QtGui.QMessageBox, self.button))

        self.setWindowTitle(self._('title'))
        self.setText(self._('message'))

        self.exec_()

def main():
    import sys

    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QtWidgets.QApplication(sys.argv)
    message = gui_message(sys.argv[1], sys.argv[2])
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

