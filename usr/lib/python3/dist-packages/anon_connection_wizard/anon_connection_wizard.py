#!/usr/bin/python3 -su

## Copyright (C) 2018 - 2026 ENCRYPTED SUPPORT LLC <adrelanos@whonix.org>
## See the file COPYING for copying conditions.

import sys
import signal
import os
import stat
import grp
import logging
import tempfile
import subprocess
import queue
import atexit
import fcntl
from logging.handlers import SysLogHandler, QueueHandler, QueueListener

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import QtCore, QtGui, QtWidgets

import yaml
import json
import time
import re
from pathlib import Path
import shutil

from guimessages.translations import _translations
from guimessages.guimessage import gui_message

from anon_connection_wizard import tor_status
from anon_connection_wizard import repair_torrc
from anon_connection_wizard.tor_status import cat
from anon_connection_wizard.edit_etc_resolv_conf import edit_etc_resolv_conf_add
from anon_connection_wizard.edit_etc_resolv_conf import edit_etc_resolv_conf_remove

# --- 1. NON-BLOCKING SYSLOG ---
log = logging.getLogger("AnonConnectionWizard")
log.setLevel(logging.INFO)

log_queue = queue.Queue(-1)
queue_handler = QueueHandler(log_queue)
log.addHandler(queue_handler)

syslog_handler = SysLogHandler(address='/dev/log')
syslog_handler.setFormatter(
    logging.Formatter('anon-connection-wizard[%(process)d]: %(levelname)s %(message)s')
)
listener = QueueListener(log_queue, syslog_handler)
listener.start()
atexit.register(listener.stop)

# Stderr fallback
console = logging.StreamHandler()
console.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
log.addHandler(console)

# --- 2. HARDENED BACKEND (Privileged Helper) ---
class AnonConnectionWizardBackend:
    MAX_CONFIG_SIZE = 1_048_576  # 1 MB safety limit

    def __init__(self, common_config):
        self.common = common_config

    def write_torrc(self, content: str) -> None:
        if not content or not content.strip():
            raise ValueError("Configuration content must not be empty.")

        if len(content.encode('utf-8')) > self.MAX_CONFIG_SIZE:
            raise ValueError(
                f"Configuration size ({len(content)} bytes) exceeds "
                f"maximum allowed ({self.MAX_CONFIG_SIZE} bytes)."
            )

        target_path = self.common.torrc_file_path
        target_dir = os.path.dirname(target_path)

        lock_path = os.path.join(target_dir, '.torrc.lock')
        with open(lock_path, 'w') as lock_file:
            try:
                fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise RuntimeError(
                    "Another configuration update is already in progress. "
                    "Please wait and try again."
                )

            tmp_target = tempfile.NamedTemporaryFile(
                mode='w', dir=target_dir, delete=False, encoding='utf-8'
            )

            try:
                tmp_target.write(content)
                tmp_target.flush()
                os.fsync(tmp_target.fileno())

                os.chmod(tmp_target.name, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP)
                try:
                    tor_gid = grp.getgrnam('debian-tor').gr_gid
                    os.chown(tmp_target.name, 0, tor_gid)
                except KeyError:
                    log.warning("Group 'debian-tor' not found - keeping default ownership.")
                    os.chown(tmp_target.name, 0, -1)

                tmp_target.close()
                os.replace(tmp_target.name, target_path)
                log.info("Configuration updated successfully: %s", target_path)

            except Exception:
                if os.path.exists(tmp_target.name):
                    os.remove(tmp_target.name)
                raise


def signal_handler(sig, frame):
    sys.exit(128 + sig)


class Common:
    whonix = os.path.exists('/usr/share/anon-gw-base-files/gateway')

    translations_path = '/usr/share/anon-connection-wizard/translations.yaml'

    # --- OPTION 1 FIX: UPDATED PATHS ---
    etc_torrc_d_folder_path = '/etc/torrc.d/'
    torrc_file_path = '/etc/torrc.d/40_tor_control_panel.conf'
    acw_comm_file_path = '/run/anon-connection-wizard/tor.conf'
    torrc_user_file_path = '/etc/torrc.d/50_user.conf'

    bridges_default_path = '/usr/share/anon-connection-wizard/bridges_default'

    control_cookie_path = '/run/tor/control.authcookie'
    control_socket_path = '/run/tor/control'

    use_bridges = False
    use_default_bridge = True
    bridge_type = 'obfs4'
    bridge_type_with_comment = 'obfs4'
    bridge_custom = ''

    use_proxy = False
    proxy_type = 'HTTP / HTTPS'
    proxy_ip = ''
    proxy_port = ''
    proxy_username = ''
    proxy_password = ''

    init_tor_status = ''
    disable_tor = False

    command_useBridges = 'UseBridges 1'
    command_use_custom_bridge = '# Custom Bridge is used:'
    command_obfs4 = 'ClientTransportPlugin obfs4 exec /usr/bin/obfs4proxy'
    command_fte = 'ClientTransportPlugin fte exec /usr/bin/fteproxy --managed'
    command_snowflake = 'ClientTransportPlugin snowflake exec /usr/bin/snowflake-client'
    command_meek_lite = 'ClientTransportPlugin meek_lite exec /usr/bin/obfs4proxy'
    command_webtunnel = 'ClientTransportPlugin webtunnel exec /usr/bin/obfs4proxy'
    command_bridgeInfo = 'Bridge '

    command_http = 'HTTPSProxy '
    command_httpAuth = 'HTTPSProxyAuthenticator'
    command_sock4 = 'Socks4Proxy '
    command_sock5 = 'Socks5Proxy '
    command_sock5Username = 'Socks5ProxyUsername'
    command_sock5Password = 'Socks5ProxyPassword'

    from_proxy_page_1 = True
    from_bridge_page_1 = True

    font_title = QtGui.QFont()
    font_title.setPointSize(13)
    font_title.setBold(True)
    font_title.setWeight(95)

    font_description_main = QtGui.QFont()
    font_description_main.setPointSize(11)
    font_description_main.setBold(True)
    font_description_main.setWeight(85)

    font_description_minor = QtGui.QFont()
    font_description_minor.setPointSize(10)
    font_description_minor.setBold(False)
    font_description_minor.setWeight(30)

    font_option = QtGui.QFont()
    font_option.setPointSize(11)
    font_option.setBold(True)
    font_option.setWeight(65)

    groupBox_width = 350
    groupBox_height = 345

    wizard_steps = ['connection_main_page',
                    'bridge_wizard_page_2',
                    'proxy_wizard_page_2',
                    'torrc_page',
                    'tor_status_page']

    assistance = 'For assistance, visit torproject.org/about/contact.html#support'


class ConnectionMainPage(QtWidgets.QWizardPage):
    def __init__(self):
        super(ConnectionMainPage, self).__init__()

        self.steps = Common.wizard_steps
        self.verticalLayout = QtWidgets.QVBoxLayout(self)
        self.groupBox = QtWidgets.QGroupBox(self)
        self.label = QtWidgets.QLabel(self.groupBox)
        self.label_2 = QtWidgets.QLabel(self.groupBox)
        self.pushButton_1 = QtWidgets.QRadioButton(self.groupBox)
        self.label_4 = QtWidgets.QLabel(self.groupBox)
        self.pushButton_2 = QtWidgets.QRadioButton(self.groupBox)
        self.label_5 = QtWidgets.QLabel(self.groupBox)
        self.pushButton_3 = QtWidgets.QRadioButton(self.groupBox)

        self.verticalLayout.addWidget(self.groupBox)
        self.setupUi()

    def setupUi(self):
        self.groupBox.setMinimumSize(QtCore.QSize(350, 330))
        self.groupBox.setGeometry(QtCore.QRect(0, 20, 0, 0))
        self.groupBox.setFlat(True)

        font_description_minor = Common.font_description_minor
        font_description_main = Common.font_description_main
        font_option = Common.font_option

        self.label.setGeometry(QtCore.QRect(10, 20, 530, 41))
        self.label.setWordWrap(True)
        self.label.setText('Before you connect to the Tor network, you need to provide information about this computer\'s Internet connection.')
        self.label.setFont(font_description_minor)

        self.label_2.setGeometry(QtCore.QRect(10, 65, 451, 21))
        self.label_2.setFont(font_description_main)
        self.label_2.setText('Which of the following best describes your situation?')

        self.label_3 = QtWidgets.QLabel(self.groupBox)
        self.label_3.setGeometry(QtCore.QRect(10, 90, 321, 41))
        self.label_3.setWordWrap(True)
        self.label_3.setText('I would like to connect directly to the Tor network. This will work in most situations.')
        self.label_3.setFont(font_description_minor)

        self.pushButton_1.setGeometry(QtCore.QRect(20, 133, 125, 26))
        self.pushButton_2.setGeometry(QtCore.QRect(20, 213, 125, 26))
        self.pushButton_3.setGeometry(QtCore.QRect(20, 288, 125, 26))
        self.pushButton_1.setFont(font_option)
        self.pushButton_1.setText('Connect')
        self.pushButton_1.setChecked(True)
        self.pushButton_2.setFont(font_option)
        self.pushButton_2.setText('Configure')
        self.pushButton_3.setFont(font_option)
        self.pushButton_3.setText('Disable Tor')
        self.pushButton_3.setVisible(True)

        self.label_4.setGeometry(QtCore.QRect(10, 166, 381, 41))
        self.label_4.setWordWrap(True)
        self.label_4.setText('This computer\'s Internet connection is censored or proxied. I need to configure bridges or local proxy settings.')
        self.label_4.setFont(font_description_minor)

        self.label_5.setGeometry(QtCore.QRect(10, 250, 500, 31))
        self.label_5.setWordWrap(True)
        self.label_5.setText('I do not want to connect automatically to the Tor network.<br>Next time I boot, this wizard will be started.')
        self.label_5.setFont(font_description_minor)
        self.label_5.setVisible(True)

        if Common.use_bridges or Common.use_proxy:
            self.pushButton_2.setChecked(True)
        else:
            self.pushButton_1.setChecked(True)

    def nextId(self):
        if self.pushButton_1.isChecked():
            Common.disable_tor = False
            Common.use_bridges = False
            Common.use_proxy = False
            return self.steps.index('torrc_page')
        elif self.pushButton_2.isChecked():
            Common.disable_tor = False
            return self.steps.index('bridge_wizard_page_2')
        elif self.pushButton_3.isChecked():
            Common.disable_tor = True
            return self.steps.index('tor_status_page')


class BridgesWizardPage2(QtWidgets.QWizardPage):
    def __init__(self):
        super(BridgesWizardPage2, self).__init__()

        self.steps = Common.wizard_steps

        self.bridges = ['obfs4',
                        'meek',
                        'snowflake',
                       ]

        self.layout = QtWidgets.QVBoxLayout(self)

        self.label = QtWidgets.QLabel(self)
        self.layout.addWidget(self.label)

        self.groupBox = QtWidgets.QGroupBox(self)
        self.layout.addWidget(self.groupBox)

        self.checkBox = QtWidgets.QCheckBox(self.groupBox)
        self.pushButton_show_help_censorship = QtWidgets.QPushButton(self.groupBox)

        self.horizontal_line_1 = QFrame(self.groupBox)
        self.default_button = QtWidgets.QRadioButton(self.groupBox)
        self.horizontal_line_2 = QFrame(self.groupBox)
        self.custom_button = QtWidgets.QRadioButton(self.groupBox)

        self.label_3 = QtWidgets.QLabel(self.groupBox)
        self.comboBox = QtWidgets.QComboBox(self.groupBox)

        self.label_4 = QtWidgets.QLabel(self.groupBox)
        self.custom_bridges = QtWidgets.QTextEdit(self.groupBox)
        self.pushButton_show_help_bridge = QtWidgets.QPushButton(self.groupBox)

        self.label_5 = QtWidgets.QLabel(self.groupBox)

        self.setupUi()

    def setupUi(self):
        self.label.setMinimumSize(QtCore.QSize(16777215, 35))

        font_title = Common.font_title
        font_description_main = Common.font_description_main
        font_description_minor = Common.font_description_minor

        self.label.setText('   Tor Bridges Configuration')
        self.label.setFont(font_title)
        self.label.setGeometry(QtCore.QRect(0, 0, 0, 0))

        self.checkBox.setChecked(Common.use_bridges)
        self.checkBox.stateChanged.connect(self.enable_bridge)
        self.checkBox.setText("I need Tor bridges to bypass the Tor censorship.")
        self.checkBox.setFont(font_description_main)
        self.checkBox.setGeometry(QtCore.QRect(20, 35, 430, 20))

        self.pushButton_show_help_censorship.setEnabled(True)
        self.pushButton_show_help_censorship.setGeometry(QtCore.QRect(440, 32, 90, 25))
        self.pushButton_show_help_censorship.setText('&No idea?')
        self.pushButton_show_help_censorship.clicked.connect(self.show_help_censorship)

        self.groupBox.setMinimumSize(QtCore.QSize(Common.groupBox_width, Common.groupBox_height))
        self.groupBox.setGeometry(QtCore.QRect(0, 20, 0, 0))
        self.groupBox.setFlat(True)

        self.horizontal_line_1.setFrameShape(QFrame.HLine)
        self.horizontal_line_1.setFrameShadow(QFrame.Sunken)
        self.horizontal_line_1.setGeometry(15, 65, 510, 5)

        self.default_button.setGeometry(QtCore.QRect(18, 75, 500, 24))
        self.default_button.setText('Select a built-in bridge')
        self.default_button.setFont(font_description_minor)

        self.horizontal_line_2.setFrameShape(QFrame.HLine)
        self.horizontal_line_2.setFrameShadow(QFrame.Sunken)
        self.horizontal_line_2.setGeometry(15, 140, 510, 5)

        self.custom_button.setGeometry(QtCore.QRect(18, 160, 500, 25))
        self.custom_button.setText('Provide a bridge I know')
        self.custom_button.setFont(font_description_minor)

        if Common.use_default_bridge:
            self.default_button.setChecked(True)
        else:
            self.custom_button.setChecked(True)

        self.default_button.toggled.connect(self.show_default_bridge)

        self.label_3.setGeometry(QtCore.QRect(40, 110, 106, 20))
        self.label_3.setText('Transport type:')
        self.label_3.setFont(font_description_minor)

        self.comboBox.setGeometry(QtCore.QRect(150, 107, 230, 27))
        for bridge in self.bridges:
            self.comboBox.addItem(bridge)

        if Common.use_default_bridge:
            self.comboBox.setCurrentIndex(self.bridges.index(Common.bridge_type_with_comment))

        self.label_4.setEnabled(False)
        self.label_4.setGeometry(QtCore.QRect(38, 185, 300, 20))
        self.label_4.setText('Enter one or more bridge relay (one per line).')

        self.custom_bridges.setEnabled(True)
        self.custom_bridges.setGeometry(QtCore.QRect(38, 205, 500, 76))
        self.custom_bridges.setStyleSheet("background-color:white;")
        self.custom_bridges.setLineWrapColumnOrWidth(1800)
        self.custom_bridges.setLineWrapMode(QtWidgets.QTextEdit.FixedPixelWidth)

        if not Common.use_default_bridge:
            self.custom_bridges.setText(Common.bridge_custom)

        self.pushButton_show_help_bridge.setEnabled(True)
        self.pushButton_show_help_bridge.setGeometry(QtCore.QRect(360, 160, 150, 25))
        self.pushButton_show_help_bridge.setText('&How to get Bridges?')
        self.pushButton_show_help_bridge.clicked.connect(self.show_help_bridge)

        self.label_5.setVisible(True)
        self.label_5.setGeometry(10, 300, 500, 15)
        self.label_5.setText(Common.assistance)
        self.label_5.setFont(font_description_minor)

        self.default_button.setVisible(Common.use_bridges)
        self.horizontal_line_2.setVisible(Common.use_bridges)
        self.custom_button.setVisible(Common.use_bridges)

        self.label_3.setVisible(Common.use_bridges and Common.use_default_bridge)
        self.comboBox.setVisible(Common.use_bridges and Common.use_default_bridge)

        self.label_4.setVisible(Common.use_bridges and (not Common.use_default_bridge))
        self.custom_bridges.setVisible(Common.use_bridges and (not Common.use_default_bridge))
        self.pushButton_show_help_bridge.setVisible(Common.use_bridges and (not Common.use_default_bridge))

    def nextId(self):
        if not self.checkBox.isChecked():
            Common.use_bridges = False
            return self.steps.index('proxy_wizard_page_2')
        else:
            Common.use_bridges = True

            if self.default_button.isChecked():
                bridge_type = str(self.comboBox.currentText())
                if bridge_type.startswith('obfs4'):
                    bridge_type = 'obfs4'
                elif bridge_type.startswith('meek'):
                    bridge_type = 'meek'
                    edit_etc_resolv_conf_add()
                elif bridge_type.startswith('snowflake'):
                   bridge_type = 'snowflake'
                   edit_etc_resolv_conf_add()

                Common.bridge_type = bridge_type
                Common.use_default_bridge = True
                return self.steps.index('proxy_wizard_page_2')

            elif self.custom_button.isChecked():
                Common.bridge_custom = str(self.custom_bridges.toPlainText())
                Common.use_default_bridge = False
                self.reformat_custom_bridge_input()
                if not self.valid_bridge(Common.bridge_custom):
                    return self.steps.index('bridge_wizard_page_2')
                else:
                    return self.steps.index('proxy_wizard_page_2')

    def reformat_custom_bridge_input(self):
        reformat_lines = []
        for bridge in self.custom_bridges.toPlainText().split('\n'):
            elements = bridge.split()
            try:
                while elements[0].lower() == 'bridge':
                    elements.pop(0)
            except:
                continue
            reformat_lines.append(' '.join(elements))
        self.custom_bridges.setText('\n'.join(reformat_lines))

    def valid_bridge(self, bridges):
        bridge_defined_type = bridges.split(' ')[0]
        bridge_defined_type = bridge_defined_type.lower()

        if (bridge_defined_type.startswith('obfs4')
                or bridge_defined_type.startswith('meek_lite')
                or bridge_defined_type.startswith('snowflake')
                or bridge_defined_type.startswith('webtunnel')
                or (('.' in bridge_defined_type) and (':' in bridge_defined_type))):
            return True
        else:
            return False

    def show_help_censorship(self):
        reply = QtWidgets.QMessageBox(QtWidgets.QMessageBox.NoIcon, 'Censorship Circumvention Help',
                                  '''<p><b>  Censorship Circumvention Help</b></p>
<p>If you are unable to connect to the Tor network, it could be that your Internet Service Provider is blocking Tor. Often, you can work around this problem by using Tor Bridges.</p>''', QtWidgets.QMessageBox.Ok)
        reply.exec_()

    def show_help_bridge(self):
        reply = QtWidgets.QMessageBox(QtWidgets.QMessageBox.NoIcon, 'Bridges Configuration Help',
                                  '''<p><b>  Bridge Relay Help</b></p>
<p>You may use the preconfigured, provided set of bridge addresses or you may obtain a custom set of addresses.</p>''', QtWidgets.QMessageBox.Ok)
        reply.exec_()

    def show_default_bridge(self, default_button_checked):
        if default_button_checked:
            self.label_3.setVisible(True)
            self.comboBox.setVisible(True)
            self.label_4.setVisible(False)
            self.custom_bridges.setVisible(False)
            self.pushButton_show_help_bridge.setVisible(False)
        else:
            self.label_3.setVisible(False)
            self.comboBox.setVisible(False)
            self.label_4.setVisible(True)
            self.custom_bridges.setVisible(True)
            self.pushButton_show_help_bridge.setVisible(True)

    def enable_bridge(self, state):
        self.default_button.setVisible(state)
        self.horizontal_line_2.setVisible(state)
        self.custom_button.setVisible(state)
        self.label_3.setVisible(state and self.default_button.isChecked())
        self.comboBox.setVisible(state and self.default_button.isChecked())
        self.label_4.setVisible(state and (not self.default_button.isChecked()))
        self.custom_bridges.setVisible(state and (not self.default_button.isChecked()))
        self.pushButton_show_help_bridge.setVisible(state and (not self.default_button.isChecked()))


class ProxyWizardPage2(QtWidgets.QWizardPage):
    def __init__(self):
        super(ProxyWizardPage2, self).__init__()

        translation = _translations(Common.translations_path, 'anon-connection-wizard')
        self._ = translation.gettext
        self.steps = Common.wizard_steps

        self.proxies = ['HTTP / HTTPS', 'SOCKS4', 'SOCKS5']

        self.layout = QtWidgets.QVBoxLayout(self)
        self.label = QtWidgets.QLabel(self)
        self.layout.addWidget(self.label)

        self.groupBox = QtWidgets.QGroupBox(self)
        self.layout.addWidget(self.groupBox)

        self.checkBox = QtWidgets.QCheckBox(self.groupBox)
        self.horizontal_line = QFrame(self.groupBox)
        self.label_2 = QtWidgets.QLabel(self.groupBox)
        self.label_3 = QtWidgets.QLabel(self.groupBox)
        self.comboBox = QtWidgets.QComboBox(self.groupBox)
        self.label_4 = QtWidgets.QLabel(self.groupBox)
        self.label_5 = QtWidgets.QLabel(self.groupBox)
        self.label_6 = QtWidgets.QLabel(self.groupBox)
        self.label_7 = QtWidgets.QLabel(self.groupBox)
        self.label_8 = QtWidgets.QLabel(self.groupBox)

        self.lineEdit = QtWidgets.QLineEdit(self.groupBox)
        self.lineEdit_2 = QtWidgets.QLineEdit(self.groupBox)
        self.lineEdit_3 = QtWidgets.QLineEdit(self.groupBox)
        self.lineEdit_4 = QtWidgets.QLineEdit(self.groupBox)
        self.lineEdit_4.setEchoMode(QLineEdit.Password)
        self.pushButton = QtWidgets.QPushButton(self.groupBox)

        self.setupUi()

    def setupUi(self):
        self.label.setMinimumSize(QtCore.QSize(16777215, 35))

        font_title = Common.font_title
        font_description_main = Common.font_description_main
        font_description_minor = Common.font_description_minor

        self.label.setText('   Local Proxy Configuration')
        self.label.setFont(font_title)

        self.groupBox.setMinimumSize(QtCore.QSize(Common.groupBox_width, Common.groupBox_height))
        self.groupBox.setGeometry(QtCore.QRect(0, 20, 0, 0))
        self.groupBox.setFlat(True)

        self.checkBox.setChecked(Common.use_proxy)
        self.checkBox.stateChanged.connect(self.enable_proxy)
        self.checkBox.setText("Use proxy before connecting to the Tor network")
        self.checkBox.setFont(font_description_main)
        self.checkBox.setGeometry(QtCore.QRect(20, 35, 500, 20))
        self.comboBox.currentIndexChanged[str].connect(self.option_changed)

        self.horizontal_line.setFrameShape(QFrame.HLine)
        self.horizontal_line.setFrameShadow(QFrame.Sunken)
        self.horizontal_line.setGeometry(15, 65, 510, 5)

        self.label_2.setGeometry(QtCore.QRect(20, 80, 201, 16))
        self.label_2.setText("Enter the proxy settings.")
        self.label_2.setFont(font_description_minor)

        self.label_3.setGeometry(QtCore.QRect(10, 110, 106, 20))
        self.label_3.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_3.setText("Proxy type: ")
        self.label_3.setFont(font_description_minor)

        self.comboBox.setGeometry(QtCore.QRect(118, 110, 121, 27))
        for proxy in self.proxies:
            self.comboBox.addItem(proxy)

        if Common.use_proxy:
            self.comboBox.setCurrentIndex(self.proxies.index(Common.proxy_type))

        self.label_5.setGeometry(QtCore.QRect(10, 150, 106, 20))
        self.label_5.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_5.setText("Address: ")
        self.label_5.setFont(font_description_minor)

        self.label_6.setGeometry(QtCore.QRect(10, 180, 106, 20))
        self.label_6.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_6.setText("Username: ")
        self.label_6.setFont(font_description_minor)

        self.label_7.setGeometry(QtCore.QRect(394, 150, 41, 20))
        self.label_7.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_7.setText("Port: ")
        self.label_7.setFont(font_description_minor)

        self.label_8.setGeometry(QtCore.QRect(280, 180, 70, 20))
        self.label_8.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_8.setText("Password: ")
        self.label_8.setFont(font_description_minor)

        self.lineEdit.setGeometry(QtCore.QRect(118, 150, 260, 25))
        self.lineEdit.setStyleSheet("background-color:white;")
        self.lineEdit.setPlaceholderText('Example: 127.0.0.1')
        self.lineEdit.setText(Common.proxy_ip)

        self.lineEdit_2.setGeometry(QtCore.QRect(437, 150, 60, 25))
        self.lineEdit_2.setStyleSheet("background-color:white;")
        self.lineEdit_2.setPlaceholderText('1-65535')
        self.lineEdit_2.setText(Common.proxy_port)

        self.lineEdit_3.setGeometry(QtCore.QRect(118, 180, 150, 25))
        self.lineEdit_3.setStyleSheet("background-color:white;")
        self.lineEdit_3.setPlaceholderText('Optional')
        self.lineEdit_3.setText(Common.proxy_username)

        self.lineEdit_4.setGeometry(QtCore.QRect(352, 180, 145, 25))
        self.lineEdit_4.setStyleSheet("background-color:white;")
        self.lineEdit_4.setPlaceholderText('Optional')
        self.lineEdit_4.setText(Common.proxy_password)

        self.label_4.setGeometry(QtCore.QRect(10, 280, 500, 15))
        self.label_4.setText(Common.assistance)
        self.label_4.setFont(font_description_minor)

        self.pushButton.setGeometry(QtCore.QRect(400, 235, 86, 25))
        self.pushButton.setText('&Help')
        self.pushButton.clicked.connect(self.show_help)

        self.label_2.setVisible(Common.use_proxy)
        self.label_3.setVisible(Common.use_proxy)
        self.comboBox.setVisible(Common.use_proxy)
        self.label_5.setVisible(Common.use_proxy)
        self.label_6.setVisible(Common.use_proxy)
        self.label_7.setVisible(Common.use_proxy)
        self.label_8.setVisible(Common.use_proxy)
        self.lineEdit.setVisible(Common.use_proxy)
        self.lineEdit_2.setVisible(Common.use_proxy)
        self.lineEdit_3.setVisible(Common.use_proxy)
        self.lineEdit_4.setVisible(Common.use_proxy)
        self.pushButton.setVisible(Common.use_proxy)

    def nextId(self):
        if not self.checkBox.isChecked():
            Common.use_proxy = False
            return self.steps.index('torrc_page')
        else:
            Common.use_proxy = True

            if self.valid_ip(self.lineEdit.text()) and self.valid_port(self.lineEdit_2.text()):
                proxy_type = str(self.comboBox.currentText())

                if proxy_type.startswith('SOCKS4'):
                    proxy_type = 'SOCKS4'
                elif proxy_type.startswith('SOCKS5'):
                    proxy_type = 'SOCKS5'
                elif proxy_type.startswith('HTTP / HTTPS'):
                    proxy_type = 'HTTP/HTTPS'

                Common.proxy_type = proxy_type
                Common.proxy_ip = str(self.lineEdit.text())
                Common.proxy_port = str(self.lineEdit_2.text())
                Common.proxy_username = str(self.lineEdit_3.text())
                Common.proxy_password = str(self.lineEdit_4.text())

                return self.steps.index('torrc_page')
            else:
                return self.steps.index('proxy_wizard_page_2')

    def valid_ip(self, ip):
        if ip == "" or ip.isspace():
            return False
        else:
            return True

    def valid_port(self, port):
        try:
            if int(port) >= 1 and int(port) <= 65535:
                return True
            else:
                return False
        except (ValueError, TypeError):
            return False

    def show_help(self):
        reply = QtWidgets.QMessageBox(QtWidgets.QMessageBox.NoIcon, 'Proxy Configuration Help',
                                  '''<p><b>  Proxy Help</b></p>
<p>If you do not know what these are, just leave them blank.</p>''', QtWidgets.QMessageBox.Ok)
        reply.exec_()

    def set_next_button_state(self, state):
        if state:
            self.button(QtWidgets.QWizard.NextButton).setEnabled(False)
        else:
            self.button(QtWidgets.QWizard.NextButton).setEnabled(True)

    def option_changed(self, text):
        if text == 'HTTP / HTTPS':
            self.label_6.setVisible(True)
            self.lineEdit_3.setVisible(True)
            self.label_8.setVisible(True)
            self.lineEdit_4.setVisible(True)
        elif text == 'SOCKS4':
            self.label_6.setVisible(False)
            self.lineEdit_3.setVisible(False)
            self.label_8.setVisible(False)
            self.lineEdit_4.setVisible(False)
        elif text == 'SOCKS5':
            self.label_6.setVisible(True)
            self.lineEdit_3.setVisible(True)
            self.label_8.setVisible(True)
            self.lineEdit_4.setVisible(True)

    def enable_proxy(self, state):
        self.label_2.setVisible(state)
        self.label_3.setVisible(state)
        self.comboBox.setVisible(state)
        self.label_5.setVisible(state)
        self.label_6.setVisible(state)
        self.label_7.setVisible(state)
        self.label_8.setVisible(state)
        self.lineEdit.setVisible(state)
        self.lineEdit_2.setVisible(state)
        self.lineEdit_3.setVisible(state)
        self.lineEdit_4.setVisible(state)
        self.pushButton.setVisible(state)


class TorrcPage(QtWidgets.QWizardPage):
    def __init__(self):
        super(TorrcPage, self).__init__()
        self.steps = Common.wizard_steps
        self.layout = QtWidgets.QVBoxLayout(self)
        self.label = QtWidgets.QLabel(self)
        self.layout.addWidget(self.label)
        self.groupBox = QtWidgets.QGroupBox(self)
        self.layout.addWidget(self.groupBox)

        self.label_2 = QtWidgets.QLabel(self.groupBox)
        self.label_3 = QtWidgets.QLabel(self.groupBox)
        self.label_4 = QtWidgets.QLabel(self.groupBox)
        self.label_5 = QtWidgets.QLabel(self.groupBox)
        self.label_6 = QtWidgets.QLabel(self.groupBox)
        self.label_7 = QtWidgets.QLabel(self.groupBox)
        self.pushButton = QtWidgets.QPushButton(self.groupBox)
        self.horizontal_line = QFrame(self.groupBox)
        self.torrc = QtWidgets.QTextBrowser(self.groupBox)

        self.show_detail = False
        self.setupUi()

    def setupUi(self):
        font_title = Common.font_title
        font_description_main = Common.font_description_main
        font_description_minor = Common.font_description_minor
        font_option = Common.font_option

        self.label.setText('   Summary')
        self.label.setFont(font_title)
        self.label.setGeometry(QtCore.QRect(0, 0, 0, 0))

        self.groupBox.setMinimumSize(QtCore.QSize(Common.groupBox_width, Common.groupBox_height))
        self.groupBox.setGeometry(QtCore.QRect(0, 20, 0, 0))
        self.groupBox.setFlat(True)

        self.label_2.setGeometry(QtCore.QRect(80, 20, 100, 50))
        self.label_2.setText(" Status: ")
        self.label_2.setFont(font_description_minor)

        self.label_3.setGeometry(QtCore.QRect(140, 20, 500, 50))
        self.label_3.setText("Probably an error occurred")
        self.label_3.setFont(font_option)

        self.label_4.setGeometry(QtCore.QRect(80, 47, 100, 50))
        self.label_4.setText("Bridges: ")
        self.label_4.setFont(font_description_minor)

        self.label_5.setGeometry(QtCore.QRect(140, 47, 500, 50))
        self.label_5.setText("Custom vanilla")
        self.label_5.setFont(font_option)

        self.label_6.setGeometry(QtCore.QRect(80, 75, 100, 50))
        self.label_6.setText("   Proxy: ")
        self.label_6.setFont(font_description_minor)

        self.label_7.setGeometry(QtCore.QRect(140, 75, 500, 50))
        self.label_7.setText("Probably an error occurred")
        self.label_7.setFont(font_option)

        self.setLayout(self.layout)

        self.pushButton.setEnabled(True)
        self.pushButton.setGeometry(QtCore.QRect(430, 100, 86, 25))
        self.pushButton.setText('&Details')
        self.pushButton.clicked.connect(self.detail)

        self.horizontal_line.setFrameShape(QFrame.HLine)
        self.horizontal_line.setFrameShadow(QFrame.Sunken)
        self.horizontal_line.setGeometry(15, 130, 510, 5)

        self.torrc.setVisible(self.show_detail)
        self.torrc.setGeometry(QtCore.QRect(20, 145, 500, 190))
        self.torrc.setStyleSheet("background-color:white;")
        self.torrc.setLineWrapColumnOrWidth(1500)
        self.torrc.setLineWrapMode(QtWidgets.QTextEdit.FixedPixelWidth)

    def nextId(self):
        return self.steps.index('tor_status_page')

    def detail(self):
        self.show_detail = not self.show_detail
        self.torrc.setVisible(self.show_detail)
        if self.show_detail:
            self.pushButton.setText('&Less')
        else:
            self.pushButton.setText('&Details')


class TorStatusPage(QtWidgets.QWizardPage):
    def __init__(self):
        super(TorStatusPage, self).__init__()
        self.steps = Common.wizard_steps
        self.bootstrap_text = QtWidgets.QLabel(self)
        self.text = QtWidgets.QLabel(self)
        self.bootstrap_progress = QtWidgets.QProgressBar(self)
        self.layout = QtWidgets.QGridLayout()
        self.setupUi()

    def setupUi(self):
        font_description_main = Common.font_description_main

        self.text.setFont(font_description_main)
        self.text.setWordWrap(True)
        self.text.setAlignment(QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.text.setMinimumSize(0, 290)

        self.bootstrap_progress.setMinimumSize(400, 0)
        self.bootstrap_progress.setMinimum(0)
        self.bootstrap_progress.setMaximum(100)
        self.bootstrap_progress.setVisible(False)

        self.layout.addWidget(self.text, 0, 1, 1, 2)
        self.layout.addWidget(self.bootstrap_progress, 1, 1, 1, 1)
        self.setLayout(self.layout)


class TorBootstrap(QtCore.QThread):
    signal = QtCore.pyqtSignal(str, int)

    def __init__(self, main):
        QtCore.QThread.__init__(self, parent=None)
        self.previous_status = ''
        self.tag_phase = {
            'starting': 'Starting',
            'conn': 'Connecting to a relay',
            'conn_dir': 'Connecting to a relay directory',
            'conn_done_pt': "Connected to pluggable transport",
            'handshake_dir': 'Finishing handshake with directory server',
            'onehop_create': 'Establishing an encrypted directory connection',
            'requesting_status': 'Retrieving network status',
            'loading_status': 'Loading network status',
            'loading_keys': 'Loading authority certificates',
            'enough_dirinfo': 'Loaded enough directory info to build circuits',
            'ap_conn': 'Connecting to a relay to build circuits',
            'ap_conn_done': 'Connected to a relay to build circuits',
            'ap_conn_done_pt': 'Connected to pluggable transport to build circuits',
            'ap_handshake': 'Finishing handshake with a relay to build circuits',
            'ap_handshake_done': 'Handshake finished with a relay to build circuits',
            'requesting_descriptors': 'Requesting relay information',
            'loading_descriptors': 'Loading relay information',
            'conn_or': 'Connecting to the Tor network',
            'conn_done': "Connected to a relay",
            'handshake': "Handshaking with a relay",
            'handshake_or': 'Finishing handshake with first hop',
            'circuit_create': 'Establishing a Tor circuit',
            'done': 'Connected to the Tor network!'
        }

    def connect_to_control_port(self):
        import stem
        import stem.control
        import stem.socket

        bootstrap_phase = 'Constructing Tor Controller...'
        bootstrap_percent = 0
        self.signal.emit(bootstrap_phase, bootstrap_percent)

        count=0
        while not os.path.exists(Common.control_socket_path) and count < 5:
            count += 0.2
            time.sleep(0.2)

        tor_controller = None
        try:
            tor_controller = stem.control.Controller.from_socket_file(Common.control_socket_path)
        except stem.SocketError:
            print('Construct Tor Controller Failed: unable to establish a connection')
            bootstrap_phase = 'no_controller'
            bootstrap_percent = 0
            self.signal.emit(bootstrap_phase, bootstrap_percent)
            time.sleep(10)
            return None

        bootstrap_phase = 'Authenticating the Tor Controller...'
        bootstrap_percent = 0
        self.signal.emit(bootstrap_phase, bootstrap_percent)

        try:
            tor_controller.authenticate(Common.control_cookie_path)
        except stem.connection.IncorrectCookieSize:
            pass
        except stem.connection.UnreadableCookieFile:
            print('Tor allows for authentication by reading it a cookie file, but we cannot read that file (probably due to permissions)')
            bootstrap_phase = 'cookie_authentication_failed'
            bootstrap_percent = 0
            self.signal.emit(bootstrap_phase, bootstrap_percent)
            time.sleep(10)
            return tor_controller
        except stem.connection.CookieAuthRejected:
            pass
        except stem.connection.IncorrectCookieValue:
            pass

        return tor_controller

    def run(self):
        self.tor_controller = self.connect_to_control_port()
        if self.tor_controller is None:
            return

        if self.tor_controller.get_conf('DisableNetwork') == '1':
            self.tor_controller.set_conf('DisableNetwork', '0')
            print('Toggle DisableNetwork value to 0. Tor is now allowed to connect to the network.')

        bootstrap_percent = 0
        while bootstrap_percent < 100:
            bootstrap_status = self.tor_controller.get_info("status/bootstrap-phase")
            if bootstrap_status != self.previous_status:
                bootstrap_percent = int(re.match('.* PROGRESS=([0-9]+).*', bootstrap_status).group(1))
                bootstrap_tag = re.search(r'TAG=(.*) +SUMMARY', bootstrap_status).group(1)
                if bootstrap_tag in self.tag_phase:
                    bootstrap_phase = self.tag_phase[bootstrap_tag]
                else:
                    bootstrap_phase = "Unknown Bootstrap TAG. This is harmless. Please run this program from command line to view console output and report this."
                    print('Unknown Bootstrap TAG. Full message is shown in the very next line:')
                print(bootstrap_status)
                self.previous_status = bootstrap_status
                self.signal.emit(bootstrap_phase, bootstrap_percent)
            time.sleep(0.2)
        self.signal.emit(bootstrap_phase, bootstrap_percent)


class AnonConnectionWizard(QtWidgets.QWizard):
    def __init__(self):
        super(AnonConnectionWizard, self).__init__()

        translation = _translations(Common.translations_path, 'anon-connection-wizard')
        self._ = translation.gettext

        self.parseTorrc()
        Common.init_tor_status = tor_status.tor_status()

        self.steps = Common.wizard_steps
        self.connection_main_page = ConnectionMainPage()
        self.addPage(self.connection_main_page)
        self.bridge_wizard_page_2 = BridgesWizardPage2()
        self.addPage(self.bridge_wizard_page_2)
        self.proxy_wizard_page_2 = ProxyWizardPage2()
        self.addPage(self.proxy_wizard_page_2)
        self.torrc_page = TorrcPage()
        self.addPage(self.torrc_page)
        self.tor_status_page = TorStatusPage()
        self.addPage(self.tor_status_page)

        self.bridges = []
        self.proxy_type = ''
        self.tor_status = ''
        self.bootstrap_done = False
        self.generated_torrc_content = ""

        self.setupUi()

    def process_connection_request(self, config_string: str) -> bool:
        if not config_string or not config_string.strip():
            QMessageBox.critical(self, "Error", "No configuration to write.")
            return False

        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            proc = subprocess.Popen(
                ['pkexec', sys.executable, __file__, '--helper'],
                stdin=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            _, err = proc.communicate(input=config_string, timeout=15)
        except subprocess.TimeoutExpired:
            QApplication.restoreOverrideCursor()
            log.critical("pkexec helper timed out.")
            QMessageBox.critical(self, "Timeout", "The configuration process timed out.\n\nPlease try again.")
            return False
        except FileNotFoundError:
            QApplication.restoreOverrideCursor()
            log.critical("pkexec not found - privilege separation unavailable.")
            QMessageBox.critical(self, "System Error", "Privilege escalation tool (pkexec) is missing.\nCannot update Tor configuration.")
            return False
        except Exception as e:
            QApplication.restoreOverrideCursor()
            log.exception("Unexpected error during helper launch: %s", e)
            QMessageBox.critical(self, "Error", f"Unexpected error: {e}")
            return False
        finally:
            QApplication.restoreOverrideCursor()

        if proc.returncode != 0:
            log.error("Helper returned %d: %s", proc.returncode, err.strip())
            QMessageBox.critical(self, "Configuration Error",
                                 f"Unable to update Tor configuration.\n\nDetails:\n{err.strip()}")
            return False

        return True

    def setupUi(self):
        self.setWindowIcon(QtGui.QIcon("/usr/share/anon-connection-wizard/advancedsettings.ico"))
        self.setWindowTitle('Anon Connection Wizard')
        self.setFixedSize(580, 450)

        self.button(QtWidgets.QWizard.BackButton).clicked.connect(self.back_button_clicked)
        self.button(QtWidgets.QWizard.NextButton).clicked.connect(self.next_button_clicked)
        self.button(QtWidgets.QWizard.CancelButton).clicked.connect(self.cancel_button_clicked)

        self.button(QtWidgets.QWizard.BackButton).setVisible(False)
        self.button(QtWidgets.QWizard.BackButton).setEnabled(False)

        self.button(QtWidgets.QWizard.FinishButton).clicked.connect(self.finish_button_clicked)

        self.button(QtWidgets.QWizard.CancelButton).setVisible(True)
        self.button(QtWidgets.QWizard.CancelButton).setEnabled(True)
        self.button(QtWidgets.QWizard.CancelButton).setText('Quit')
        self.exec_()

    def update_bootstrap(self, bootstrap_phase, bootstrap_percent):
        self.tor_status_page.bootstrap_progress.setValue(bootstrap_percent)
        if bootstrap_percent == 100:
            self.tor_status_page.text.setText('<p><b>Tor bootstrapping done</b></p>Bootstrap phase: {0}'.format(bootstrap_phase))
            self.bootstrap_done = True
            self.show_finish_button()
        else:
            self.tor_status_page.text.setText('<p><b>Bootstrapping Tor...</b></p>Bootstrap phase: {0}'.format(bootstrap_phase))

        if bootstrap_phase == 'no_controller':
            self.bootstrap_thread.terminate()
            QMessageBox.warning(self, 'Tor Controller Not Constructed', 'Tor controller cannot be constructed.')
            sys.exit(1)
        elif bootstrap_phase == 'cookie_authentication_failed':
            self.bootstrap_thread.terminate()
            QMessageBox.warning(self, 'Tor Controller Authentication Failed',
                                'Tor allows for authentication by reading it a cookie file, but we cannot read that file (probably due to permissions)')
            sys.exit(1)

    def next_button_clicked(self):
        self.bridge_wizard_page_2.reformat_custom_bridge_input()
        if self.currentId() == self.steps.index('connection_main_page'):
            self.button(QtWidgets.QWizard.CancelButton).setVisible(True)
            self.button(QtWidgets.QWizard.FinishButton).setVisible(False)
            Common.from_bridge_page_1 = True
            Common.from_proxy_page_1 = True

        if self.currentId() == self.steps.index('bridge_wizard_page_2'):
            if not Common.from_bridge_page_1:
                if self.bridge_wizard_page_2.checkBox.isChecked() and self.bridge_wizard_page_2.custom_button.isChecked():
                    if not self.bridge_wizard_page_2.valid_bridge((self.bridge_wizard_page_2.custom_bridges.toPlainText())):
                        self.reply = QtWidgets.QMessageBox(QtWidgets.QMessageBox.NoIcon, 'Warning',
                            '''<p><b>  Custom bridge list is blank or invalid</b></p>
                            <p> Please input valid custom bridges or use provided bridges instead.</p>''', QtWidgets.QMessageBox.Ok)
                        self.reply.exec_()

            Common.from_bridge_page_1 = False
            Common.from_proxy_page_1 = True

        if self.currentId() == self.steps.index('proxy_wizard_page_2'):
            if not Common.from_proxy_page_1:
                if self.proxy_wizard_page_2.checkBox.isChecked():
                    if not (
                    self.proxy_wizard_page_2.valid_ip(self.proxy_wizard_page_2.lineEdit.text()) and\
                    self.proxy_wizard_page_2.valid_port(self.proxy_wizard_page_2.lineEdit_2.text())
                    ):
                        self.reply = QtWidgets.QMessageBox(QtWidgets.QMessageBox.NoIcon, 'Warning',
                        '''<p><b>  Please input valid Address and Port number.</b></p>
                        <p> The Address should look like: 127.0.0.1 or localhost</p>
                        <p> The Port number should be an integer between 1 and 65535</p>''', QtWidgets.QMessageBox.Ok)
                        self.reply.exec_()
            Common.from_proxy_page_1 = False

        if self.currentId() == self.steps.index('torrc_page'):
            self.button(QtWidgets.QWizard.BackButton).setVisible(True)
            self.button(QtWidgets.QWizard.CancelButton).setVisible(True)
            self.button(QtWidgets.QWizard.FinishButton).setVisible(False)

            self.generated_torrc_content = self.build_torrc_config()

            if not Common.disable_tor:
                self.torrc_page.label_3.setText('Tor will be enabled.')
                if not Common.use_bridges:
                    self.torrc_page.label_5.setText('None Selected')
                else:
                    if Common.use_default_bridge:
                        if Common.bridge_type == 'obfs4':
                            self.torrc_page.label_5.setText('Provided obfs4')
                        elif Common.bridge_type == 'meek':
                            self.torrc_page.label_5.setText('Provided meek')
                        elif Common.bridge_type == 'snowflake':
                            self.torrc_page.label_5.setText('Provided snowflake')
                    else:
                        if Common.bridge_custom.lower().startswith('obfs4'):
                            self.torrc_page.label_5.setText('Custom obfs4')
                        elif Common.bridge_custom.lower().startswith('meek_lite'):
                            self.torrc_page.label_5.setText('Custom meek_lite')
                        elif Common.bridge_custom.lower().startswith('snowflake'):
                            self.torrc_page.label_5.setText('Custom snowflake')
                        elif Common.bridge_custom.lower().startswith('webtunnel'):
                            self.torrc_page.label_5.setText('Custom webtunnel')
                        else:
                            self.torrc_page.label_5.setText('Custom vanilla')

                self.torrc_page.label_7.setText('Tor will be enabled.')
                self.torrc_page.torrc.setPlainText(self.generated_torrc_content)
            else:
                self.torrc_page.label_3.setText('Tor will be disabled.')
                self.torrc_page.label_4.setVisible(False)
                self.torrc_page.label_5.setVisible(False)
                self.torrc_page.label_6.setVisible(False)
                self.torrc_page.label_7.setVisible(False)
                self.torrc_page.pushButton.setVisible(False)
                torrc_text = ""
                try:
                    torrc_text = open(Common.torrc_file_path).read()
                except:
                    torrc_text = "(could not read current configuration)"
                self.torrc_page.torrc.setPlainText(torrc_text)

            if not Common.use_proxy:
                self.torrc_page.label_7.setText('None Selected')
            else:
                if Common.proxy_type == 'HTTP/HTTPS':
                    self.torrc_page.label_7.setText('HTTP(S)  {0} : {1}'.format(Common.proxy_ip, Common.proxy_port))
                elif Common.proxy_type == 'SOCKS4':
                    self.torrc_page.label_7.setText('Socks4  {0} : {1}'.format(Common.proxy_ip, Common.proxy_port))
                elif Common.proxy_type == 'SOCKS5':
                    self.torrc_page.label_7.setText('Socks5  {0} : {1}'.format(Common.proxy_ip, Common.proxy_port))

        if self.currentId() == self.steps.index('tor_status_page'):
            self.tor_status_page.text.setText('')
            self.button(QtWidgets.QWizard.BackButton).setVisible(True)
            self.button(QtWidgets.QWizard.CancelButton).setVisible(True)
            self.button(QtWidgets.QWizard.FinishButton).setVisible(False)

            if not Common.disable_tor:
                if not self.process_connection_request(self.generated_torrc_content):
                    self.tor_status_page.bootstrap_progress.setVisible(False)
                    self.tor_status_page.text.setText(
                        '<p><b>Failed to save Tor configuration.</b></p>'
                        '<p>Privilege escalation failed or was cancelled. Please check the system logs.</p>')
                    self.show_finish_button()
                    return

                self.tor_status_page.bootstrap_progress.setVisible(True)

                self.tor_status_result = tor_status.set_enabled()
                self.tor_status = self.tor_status_result[0]
                self.tor_status_code = str(self.tor_status_result[1])

                if self.tor_status == 'tor_enabled' or self.tor_status == 'tor_already_enabled':
                    self.tor_status_page.bootstrap_progress.setVisible(True)
                    self.bootstrap_thread = TorBootstrap(self)
                    self.bootstrap_thread.signal.connect(self.update_bootstrap)
                    self.bootstrap_thread.start()
                elif self.tor_status == 'cannot_connect':
                    print('tor_status: ' + self.tor_status + self.tor_status_code, file=sys.stderr)
                    self.tor_status_page.bootstrap_progress.setVisible(False)
                    self.tor_status_page.text.setText('<p><b>Tor failed to (re)start.</b></p>\
                    <p>Job for tor@default.service failed because the control process \
                    exited with error code.</p>' +
                    'Error Code: ' + self.tor_status_code + '\n' +
                    '<p>Often, this is because of your torrc file(s) has corrupted settings.</p>' +
                    '<p>See "systemctl status tor@default.service" and \
                    "journalctl -xe" for details.</p>\
                    <p>You may not be able to use any network facing application for now.</p>')
                else:
                    print('Unexpected tor_status: ' + self.tor_status + '\n' +
                        "Error Code:" + self.tor_status_code, file=sys.stderr)
                    self.tor_status_page.bootstrap_progress.setVisible(False)
                    self.tor_status_page.text.setText('<p><b>Unexpected Exception.</b></p>\
                    <p>You may not be able to use any network facing application for now.</p>\
                    Unexpected exception reported from tor_status module:' + self.tor_status\
                    + '\n' + "Error Code:" + self.tor_status_code)

            else:
                self.tor_status = tor_status.set_disabled()
                edit_etc_resolv_conf_remove()
                self.tor_status_page.bootstrap_progress.setVisible(False)
                self.tor_status_page.text.setVisible(True)
                self.tor_status_page.text.setText('<p><b>Tor is disabled.</b></p>\
                <p>You will not be able to use any network facing application.</p>\
                <p>You can enable Tor at any moment using <i>Anon Connection Wizard</i> \
                from your application launcher, or from a terminal:\
                <blockquote><code>anon-connection-wizard</code></blockquote> \
                or even simply press the <i>Back button</i> and select another option right now.')
                self.show_finish_button()

    def back_button_clicked(self):
        try:
            if self.bootstrap_thread:
                self.bootstrap_thread.terminate()
                self.bootstrap_thread = False

                if Common.init_tor_status == 'tor_enabled':
                    pass
                elif Common.init_tor_status == 'tor_disabled':
                    tor_status.set_disabled()
        except AttributeError:
            pass

        if self.currentId() == self.steps.index('connection_main_page'):
            Common.from_bridge_page_1 = True
            Common.from_proxy_page_1 = True
            self.bootstrap_done = False
            self.button(QtWidgets.QWizard.FinishButton).setVisible(False)
            self.button(QtWidgets.QWizard.CancelButton).setVisible(True)

        if self.currentId() == self.steps.index('bridge_wizard_page_2'):
            Common.from_proxy_page_1 = True

    def cancel_button_clicked(self):
        try:
            if self.bootstrap_thread:
                self.bootstrap_thread.terminate()
                tor_status.set_disabled()

            if Common.init_tor_status == 'tor_enabled':
                pass
            elif Common.init_tor_status == 'tor_disabled':
                tor_status.set_disabled()
        except AttributeError:
            pass

    def finish_button_clicked(self):
        return True

    def show_finish_button(self):
        if self.bootstrap_done or Common.disable_tor:
            self.button(QtWidgets.QWizard.CancelButton).setVisible(False)
            self.button(QtWidgets.QWizard.FinishButton).setVisible(True)
            self.button(QtWidgets.QWizard.FinishButton).setFocus()

    def closeEvent(self, event):
        self.cancel_button_clicked()
        event.accept()

    def build_torrc_config(self) -> str:
        try:
            repair_torrc.repair_torrc()
        except PermissionError:
            log.warning("repair_torrc() requires root privileges and was skipped.")
            QMessageBox.warning(self, "Permission Error",
                                "The repair step could not be completed due to insufficient permissions.\n"
                                "The configuration will be generated anyway.")
        except Exception as e:
            log.error("repair_torrc() failed: %s", e)

        lines = []
        lines.append("# This file is generated by anon-connection-wizard.")
        lines.append("# User configuration should go to {}, not here.".format(Common.torrc_user_file_path))
        lines.append("")

        if Common.use_bridges:
            lines.append(Common.command_useBridges)
            if Common.use_default_bridge:
                if Common.bridge_type == 'obfs4':
                    lines.append(Common.command_obfs4)
                elif Common.bridge_type == 'meek':
                    lines.append(Common.command_meek_lite)
                elif Common.bridge_type == 'snowflake':
                    lines.append(Common.command_snowflake)
                
                try:
                    with open(Common.bridges_default_path) as bf:
                        bridges_data = json.load(bf)
                        for bridge in bridges_data['bridges'][Common.bridge_type]:
                            lines.append(bridge)
                except Exception as e:
                    log.error("Failed to load default bridges: %s", e)
            else:
                lines.append(Common.command_use_custom_bridge)
                if Common.bridge_custom.lower().startswith('obfs4'):
                    lines.append(Common.command_obfs4)
                elif Common.bridge_custom.lower().startswith('fte'):
                    lines.append(Common.command_fte)
                elif Common.bridge_custom.lower().startswith('meek_lite'):
                    lines.append(Common.command_meek_lite)
                elif Common.bridge_custom.lower().startswith('snowflake'):
                    lines.append(Common.command_snowflake)
                elif Common.bridge_custom.lower().startswith('webtunnel'):
                    lines.append(Common.command_webtunnel)

                for bridge in Common.bridge_custom.split('\n'):
                    bridge = bridge.strip()
                    if bridge:
                        lines.append('Bridge ' + bridge)

        if Common.use_proxy:
            if Common.proxy_type == 'HTTP/HTTPS':
                lines.append('HTTPSProxy {}:{}'.format(Common.proxy_ip, Common.proxy_port))
                if Common.proxy_username:
                    lines.append('HTTPSProxyAuthenticator {}:{}'.format(Common.proxy_username, Common.proxy_password))
            elif Common.proxy_type == 'SOCKS4':
                lines.append('Socks4Proxy {}:{}'.format(Common.proxy_ip, Common.proxy_port))
            elif Common.proxy_type == 'SOCKS5':
                lines.append('Socks5Proxy {}:{}'.format(Common.proxy_ip, Common.proxy_port))
                if Common.proxy_username:
                    lines.append('Socks5ProxyUsername {}'.format(Common.proxy_username))
                    if Common.proxy_password:
                        lines.append('Socks5ProxyPassword {}'.format(Common.proxy_password))

        return "\n".join(lines) + "\n"

    def parseTorrc(self):
        if not os.path.exists(Common.torrc_file_path):
            print("Tor config file does not exist yet: " + Common.torrc_file_path)

        if os.path.exists(Common.torrc_file_path):
            with open(Common.torrc_file_path, 'r') as f:
                for line in f:
                    if line.startswith(Common.command_use_custom_bridge):
                        Common.use_default_bridge = False
                    elif line.startswith('#'):
                        pass
                    elif line.startswith(Common.command_useBridges):
                        Common.use_bridges = True
                    elif line.startswith(Common.command_bridgeInfo):
                        Common.bridge_type = line.split(' ')[1]
                        Common.bridge_custom += ' '.join(line.split(' ')[1:])
                    elif line.startswith(Common.command_http):
                        Common.use_proxy = True
                        Common.proxy_type = 'HTTP / HTTPS'
                        Common.proxy_ip = line.split(' ')[1].split(':')[0]
                        Common.proxy_port = line.split(' ')[1].split(':')[1].split('\n')[0]
                    elif line.startswith(Common.command_httpAuth):
                        Common.proxy_username = line.split(' ')[1].split(':')[0]
                        Common.proxy_password = line.split(' ')[1].split(':')[1]
                    elif line.startswith(Common.command_sock4):
                        Common.use_proxy = True
                        Common.proxy_type = 'SOCKS4'
                        Common.proxy_ip = line.split(' ')[1].split(':')[0]
                        Common.proxy_port = line.split(' ')[1].split(':')[1].split('\n')[0]
                    elif line.startswith(Common.command_sock5):
                        Common.use_proxy = True
                        Common.proxy_type = 'SOCKS5'
                        Common.proxy_ip = line.split(' ')[1].split(':')[0]
                        Common.proxy_port = line.split(' ')[1].split(':')[1].split('\n')[0]
                    elif line.startswith(Common.command_sock5Username):
                        Common.proxy_username = line.split(' ')[1]
                    elif line.startswith(Common.command_sock5Password):
                        Common.proxy_password = line.split(' ')[1]

        if Common.bridge_type == 'obfs4':
            Common.bridge_type_with_comment = 'obfs4'
        elif Common.bridge_type == 'meek':
            Common.bridge_type_with_comment = 'meek'


# --- 4. ENTRY POINT ---
def main():
    if '--helper' in sys.argv:
        content = sys.stdin.read()
        try:
            backend = AnonConnectionWizardBackend(Common)
            backend.write_torrc(content)
            sys.exit(0)
        except ValueError as ve:
            log.error("Invalid input: %s", ve)
            sys.exit(1)
        except RuntimeError as re:
            log.error("Runtime error: %s", re)
            sys.exit(2)
        except PermissionError:
            log.critical("Helper lacks write permission for torrc path.")
            sys.exit(3)
        except Exception:
            log.exception("Fatal error in privileged helper.")
            sys.exit(4)

    if os.geteuid() == 0:
        print('anon_connection_wizard.py: ERROR: Do not run with sudo / as root!')
        sys.exit(1)

    app = QtWidgets.QApplication(sys.argv)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    timer = QtCore.QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    QtWidgets.QApplication.setStyle('cleanlooks')
    wizard = AnonConnectionWizard()


if __name__ == "__main__":
    main()
