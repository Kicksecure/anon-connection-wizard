#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-

# The next two blocks are similar to whonix-setup-wizard. However, it seems to be repetitive, isn't it?
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from PyQt5 import QtCore, QtGui, QtWidgets

from subprocess import call, Popen
import os, yaml
import json
import sys
import time
import re
import shutil
import distutils.spawn

from guimessages.translations import _translations
from guimessages.guimessage import gui_message

from anon_connection_wizard import tor_status
#import tor_status

class Common:
    '''
    Variables and constants used through all the classes
    '''
    translations_path ='/usr/share/translations/whonix_setup.yaml'

    torrc_file_path = '/etc/torrc.d/anon_connection_wizard.torrc'

    ## TODO: this file path may not be standard
    torrc_tmp_file_path = '/etc/tor/anon_connection_wizard.torrc.tmp'

    bridges_default_path = '/usr/share/anon-connection-wizard/bridges_default'
    # well_known_proxy_setting_default_path = '/usr/share/anon-connection-wizard/well_known_proxy_settings'
    use_bridges = False
    use_proxy = False
    use_default_bridge = True
    bridge_type = ''
    bridge_custom = ''
    proxy_type = ''
    proxy_ip = ''
    proxy_port = ''
    proxy_username = ''
    proxy_password = ''

    disable_tor = False

    original_torrc = True  # This shows the state where we need to inform user the torrc is not the orginal one, like what Tor launcher has been doing

    if not os.path.exists('/var/cache/whonix-setup-wizard/status-files'):
        os.makedirs('/var/cache/whonix-setup-wizard/status-files')

    if not os.path.exists('/var/cache/whonix-setup-wizard/status-files/whonix_connection.done'):
        ## "not whonix_connection.done" is required once at first run to get a copy of the original torrc.
        ## It does not matter whether the wizard is completed or not, so we can write it here.
        #shutil.copy(torrc_file_path, '/etc/tor/torrc.orig')
        f = open('/var/cache/whonix-setup-wizard/status-files/whonix_connection.done', 'w')
        f.close()
        
    wizard_steps = ['connection_main_page',
                    'bridge_wizard_page_1',
                    'bridge_wizard_page_2',
                    'proxy_wizard_page_1',
                    'proxy_wizard_page_2',
                    'torrc_page',
                    'tor_status_page']
    # TODO: may replace the URL with a better one for usability and accessibility
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

        '''
        self.pushButton = QtWidgets.QPushButton(self.groupBox)
        self.show_disable = False
        '''
        
        self.verticalLayout.addWidget(self.groupBox)

        self.setupUi()

    def setupUi(self):
        self.groupBox.setFlat(True)
        self.groupBox.setMinimumSize(QtCore.QSize(530, 320))

        self.label.setGeometry(QtCore.QRect(10, 20, 530, 41))
        self.label.setWordWrap(True)
        self.label.setText('Before you connect to the Tor network, you need to provide information about this computer\'s Internet connection.')

        self.label_2.setGeometry(QtCore.QRect(10, 60, 431, 21))
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.label_2.setFont(font)
        self.label_2.setText('Which of the following best describes your situation?')

        self.label_3 = QtWidgets.QLabel(self.groupBox)
        self.label_3.setGeometry(QtCore.QRect(10, 85, 321, 41))
        self.label_3.setWordWrap(True)
        self.label_3.setText('I would like to connect directly to the Tor network. This will work in most situations.')

        self.pushButton_1.setGeometry(QtCore.QRect(20, 123, 110, 26))
        self.pushButton_2.setGeometry(QtCore.QRect(20, 203, 110, 26))
        self.pushButton_3.setGeometry(QtCore.QRect(20, 283, 110, 26))
        self.pushButton_1.setFont(font)
        self.pushButton_1.setText('Connect')
        self.pushButton_1.setChecked(True)
        self.pushButton_2.setFont(font)
        self.pushButton_2.setText('Configure')
        self.pushButton_3.setFont(font)
        self.pushButton_3.setText('Disable Tor')
        self.pushButton_3.setVisible(True)

        self.label_4.setGeometry(QtCore.QRect(10, 165, 381, 41))
        self.label_4.setWordWrap(True)
        self.label_4.setText('This computer\'s Internet connection is censored or proxied. I need to configure bridges or local proxy settings.')

        self.label_5.setGeometry(QtCore.QRect(10, 250, 500, 31))
        self.label_5.setWordWrap(True)
        self.label_5.setText('I do not want to connect automatically to the Tor network.<br>Next time I boot, this wizard will be started.')
        self.label_5.setVisible(True)

        '''
        self.pushButton.setGeometry(QtCore.QRect(430, 285, 80, 25))
        self.pushButton.setText('&Advanced')
        self.pushButton.clicked.connect(self.show_disable_tor)

    def show_disable_tor(self):
        self.show_disable = not self.show_disable
        self.pushButton_3.setVisible(self.show_disable)
        self.label_5.setVisible(self.show_disable)
        if self.show_disable:
            self.pushButton.setText('&Less')
        else:
            self.pushButton.setText('&Advanced')
        '''

    def nextId(self):
        if self.pushButton_1.isChecked():
            Common.disable_tor = False
            return self.steps.index('torrc_page')
        elif self.pushButton_2.isChecked():
            Common.disable_tor = False
            return self.steps.index('bridge_wizard_page_1')
        elif self.pushButton_3.isChecked():
            Common.disable_tor = True
            return self.steps.index('torrc_page')


class BridgesWizardPage1(QtWidgets.QWizardPage):
    def __init__(self):
        super(BridgesWizardPage1, self).__init__()

        translation = _translations(Common.translations_path, 'whonixsetup')
        self._ = translation.gettext

        self.steps = Common.wizard_steps

        self.layout = QtWidgets.QVBoxLayout(self)
        self.label = QtWidgets.QLabel(self)
        self.layout.addWidget(self.label)

        self.label_2 = QtWidgets.QLabel(self)
        self.layout.addWidget(self.label_2)

        self.group_box = QtWidgets.QGroupBox(self)
        self.no_button_1 = QtWidgets.QRadioButton(self.group_box)
        #self.no_button_2 = QtWidgets.QRadioButton(self.group_box)
        self.yes_button = QtWidgets.QRadioButton(self.group_box)
        self.label_3 = QtWidgets.QLabel(self.group_box)
        self.label_4 = QtWidgets.QLabel(self.group_box)
        self.layout.addWidget(self.group_box)

        self.setupUi()

    def setupUi(self):
        self.label.setMinimumSize(QtCore.QSize(16777215, 35))
        font = QtGui.QFont()
        font.setPointSize(11)
        font.setBold(True)
        font.setWeight(75)
        self.label.setFont(font)
        self.label.setText('   Tor Bridges Configuration')

        self.label_2.setMaximumSize(QtCore.QSize(16777215, 50))
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.label_2.setFont(font)
        self.label_2.setWordWrap(True)
        #self.label_2.setText('Does your Internet Service Provider (ISP) block or otherwise censor connections to the Tor network?')
        self.label_2.setText('Do you want to configure Tor bridges?')

        self.group_box.setMinimumSize(QtCore.QSize(16777215, 244))
        self.group_box.setFlat(True)
        
        self.no_button_1.setGeometry(QtCore.QRect(25, 20, 550, 30))
        self.no_button_1.setText('No. My ISP does not censor my connections to the Tor network.')
        self.no_button_1.setChecked(True)
        
        #self.no_button_2.setGeometry(QtCore.QRect(25, 50, 550, 30))
        #self.no_button_2.setText('No. I will use some third party censorship circumvention tools instead.')

        self.yes_button.setGeometry(QtCore.QRect(25, 50, 550, 30))
        self.yes_button.setText('Yes. I need Tor bridges to help me bypass the Tor censorship.')
        

        # self.label_3.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.label_3.setGeometry(10, 110, 520, 160)
        self.label_3.setTextFormat(QtCore.Qt.RichText)
        self.label_3.setWordWrap(True)
        self.label_3.setText('Tor bridges are unlisted relays that may be able to help you bypass the Tor censorship conducted by your Internet Service Provider (ISP).\n')
        self.label_4.setGeometry(10, 220, 500, 15)
        self.label_4.setText(Common.assistance)

    def nextId(self):
        if self.yes_button.isChecked():
            Common.use_bridges = True
            return self.steps.index('bridge_wizard_page_2')
        elif self.no_button_1.isChecked():
            Common.use_bridges = False
            return self.steps.index('proxy_wizard_page_1')
        #elif self.no_button_2.isChecked():
         #   Common.use_bridges = False
          #  return self.steps.index('proxy_wizard_page_2')


class BridgesWizardPage2(QtWidgets.QWizardPage):
    def __init__(self):
        super(BridgesWizardPage2, self).__init__()

        self.steps = Common.wizard_steps

        self.bridges = ['obfs4 (recommended)',
                        'obfs3'

                        # The following will be uncommented as soon as being implemented.
                        # Detail: https://github.com/Whonix/anon-connection-wizard/pull/2
                        # 'fte',
                        # 'meek-amazon',
                        # 'meek-azure'
                       ]

        self.layout = QtWidgets.QVBoxLayout(self)
        self.label = QtWidgets.QLabel(self)
        self.layout.addWidget(self.label)

        self.label_2 = QtWidgets.QLabel(self)
        self.layout.addWidget(self.label_2)

        self.groupBox = QtWidgets.QGroupBox(self)
        self.default_button = QtWidgets.QRadioButton(self.groupBox)
        self.custom_button = QtWidgets.QRadioButton(self.groupBox)
        self.label_3 = QtWidgets.QLabel(self.groupBox)
        self.comboBox = QtWidgets.QComboBox(self.groupBox)
        self.label_4 = QtWidgets.QLabel(self.groupBox)
        self.custom_bridges = QtWidgets.QTextEdit(self.groupBox)  # This is the QTextEdit box for bridges.
        self.pushButton = QtWidgets.QPushButton(self.groupBox)
        self.label_5 = QtWidgets.QLabel(self.groupBox)

        self.layout.addWidget(self.groupBox)
        self.setupUi()

    def setupUi(self):
        self.label.setMinimumSize(QtCore.QSize(16777215, 35))
        font = QtGui.QFont()
        font.setPointSize(11)
        font.setBold(True)
        font.setWeight(75)
        self.label.setFont(font)
        self.label.setText('   Tor Bridges Configuration')

        self.label_2.setMaximumSize(QtCore.QSize(16777215, 50))
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.label_2.setFont(font)
        self.label_2.setWordWrap(True)
        self.label_2.setText('You may use the provided set of bridges or you may obtain and enter a custom set of bridges.')

        self.groupBox.setMinimumSize(QtCore.QSize(16777215, 243))
        self.groupBox.setFlat(True)
        self.default_button.setGeometry(QtCore.QRect(18, 25, 500, 24))
        self.default_button.setChecked(True)
        self.default_button.setText('Connect with provided bridges')

        self.custom_button.setGeometry(QtCore.QRect(18, 82, 500, 25))
        self.custom_button.setText('Enter custom bridges')

        self.label_3.setGeometry(QtCore.QRect(38, 47, 106, 20))
        self.label_3.setText('Transport type:')

        # This is the how to make a comboBox. The variable bridges is defined above.
        # The proxy type selection in ProxyWizardPage2 can also use this method.
        self.comboBox.setGeometry(QtCore.QRect(135, 44, 181, 27))
        for bridge in self.bridges:
            self.comboBox.addItem(bridge)

        self.label_4.setEnabled(False)
        self.label_4.setGeometry(QtCore.QRect(38, 105, 300, 20))
        self.label_4.setText('Enter one or more bridge relay (one per line).')

        # TODO: The boolean value of this should be the same with self.custom_button.isChecked() Q: How to do it dynamically? A: signal-and-slot.
        # Notice that this feature is not in Tor launcher, this can be an improvement which also benefits upstream.
        # TODO: Make this QTextEdit support syntax to make it even more clear to users what should be input: https://doc.qt.io/archives/qq/qq21-syntaxhighlighter.html
        self.custom_bridges.setEnabled(True)
        self.custom_bridges.setGeometry(QtCore.QRect(38, 125, 500, 76))
        self.custom_bridges.setStyleSheet("background-color:white;")
        # Allow long input appears in one line.
        self.custom_bridges.setLineWrapColumnOrWidth(1800)
        self.custom_bridges.setLineWrapMode(QtWidgets.QTextEdit.FixedPixelWidth)
        # TODO: The next statement can not be used yet, this is because the QTextEdit does not supprot setPlaceholderText.
        # More functions need to be added to implement that: https://doc.qt.io/archives/qq/qq21-syntaxhighlighter.html
        # self.custom_bridges.setPlaceholderText('type address:port')

        self.pushButton.setGeometry(QtCore.QRect(450, 70, 86, 25))
        self.pushButton.setText('&Help')
        self.pushButton.clicked.connect(self.show_help)

        self.label_5.setGeometry(10, 220, 500, 15)
        self.label_5.setText(Common.assistance)

    def nextId(self):
        if self.default_button.isChecked():
            bridge_type = str(self.comboBox.currentText())
            if bridge_type.startswith('obfs3'):
                bridge_type = 'obfs3'
            elif bridge_type.startswith('obfs4'):
                bridge_type = 'obfs4'
            # elif bridge_type.startswith('scramblesuit'):
            #    bridge_type = 'scramblesuit'
            ''' TODO: Other options can be implemented once whonix supports them
                Detail: https://github.com/Whonix/anon-connection-wizard/pull/2
            elif bridge_type.startswith('fte'):
                bridge_type = 'fte'
            elif bridge_type.startswith('meek-amazon'):
                bridge_type = 'meek-amazon'
            elif bridge_type.startswith('meek-azure'):
                bridge_type = 'meek-azure'
            '''
            Common.bridge_type = bridge_type
            Common.use_default_bridge = True

        elif self.custom_button.isChecked():
            Common.bridge_custom = str(self.custom_bridges.toPlainText())
            Common.use_default_bridge = False

        return self.steps.index('proxy_wizard_page_1')


    def show_help(self):
        reply = QtWidgets.QMessageBox(QtWidgets.QMessageBox.NoIcon, 'Bridges Configuration Help',
                                  '''<p><b>  Bridge Relay Help</b></p>

<p>If you are unable to connect to the Tor network, it could be that your Internet Service
Provider (ISP) or another agency is blocking Tor.  Often, you can work around this problem
by using Tor Bridges, which are unlisted relays that are more difficult to block.</p>

<p>You may use the preconfigured, provided set of bridge addresses or you may obtain a
custom set of addresses by using one of these three methods:</p>

<blockquote>1.<b>Through the Web</b><br>
Use a web browser to visit https://bridges.torproject.org/options</blockquote>

<blockquote>2. <b>Through the Email Autoresponder</b><br>
Send email to bridges@torproject.org with the line 'get bridges' by itself in the body
of the message.  However, to make it harder for an attacker to learn a lot of bridge
addresses, you must send this request from one of the following email providers
(listed in order of preference):<br><br>
https://www.riseup.net, https://mail.google.com, or https://mail.yahoo.com</blockquote>

<blockquote>3. <b>Through the Help Desk</b><br>
As a last resort, you can request bridge addresses by sending a polite email
message to help@rt.torproject.org.  Please note that a person will need to respond
to each request.</blockquote>''', QtWidgets.QMessageBox.Ok)
        reply.exec_()


class ProxyWizardPage1(QtWidgets.QWizardPage):
    def __init__(self):
        super(ProxyWizardPage1, self).__init__()

        translation = _translations(Common.translations_path, 'whonixsetup')
        self._ = translation.gettext

        self.Common = Common()
        self.steps = self.Common.wizard_steps

        self.layout = QtWidgets.QVBoxLayout(self)
        self.label = QtWidgets.QLabel(self)
        self.layout.addWidget(self.label)

        self.label_2 = QtWidgets.QLabel(self)
        self.layout.addWidget(self.label_2)

        self.group_box = QtWidgets.QGroupBox(self)
        self.yes_button = QtWidgets.QRadioButton(self.group_box)
        self.no_button = QtWidgets.QRadioButton(self.group_box)
        self.label_3 = QtWidgets.QLabel(self.group_box)
        self.label_4 = QtWidgets.QLabel(self.group_box)
        self.layout.addWidget(self.group_box)

        self.setupUi()

    def setupUi(self):
        self.label.setMinimumSize(QtCore.QSize(16777215, 35))
        font = QtGui.QFont()
        font.setPointSize(11)
        font.setBold(True)
        font.setWeight(75)
        self.label.setFont(font)
        self.label.setText('   Local Proxy Configuration')

        self.label_2.setMaximumSize(QtCore.QSize(16777215, 50))
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.label_2.setFont(font)
        self.label_2.setWordWrap(True)
        self.label_2.setText('Does this computer need to use a local proxy to access the Internet?')

        self.group_box.setMinimumSize(QtCore.QSize(16777215, 250))
        self.group_box.setFlat(True)
        self.yes_button.setGeometry(QtCore.QRect(25, 30, 350, 21))
        self.yes_button.setText('Yes')
        self.no_button.setGeometry(QtCore.QRect(25, 50, 350, 21))
        self.no_button.setText('No')
        self.no_button.setChecked(True)

        # self.label_3.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.label_3.setGeometry(10, 75, 520, 60)
        self.label_3.setTextFormat(QtCore.Qt.RichText)
        self.label_3.setWordWrap(True)
        self.label_3.setText('If you are not sure how to answer this question, look at the Internet \
                              settings in your host browser to see whether it is configured to use \
                              a local proxy')

        self.label_4.setGeometry(10, 265, 500, 15)
        self.label_4.setText(Common.assistance)

    def nextId(self):
        if self.yes_button.isChecked():
            Common.use_proxy = True
            return self.steps.index('proxy_wizard_page_2')
        elif self.no_button.isChecked():
            Common.use_proxy = False
            return self.steps.index('torrc_page')


class ProxyWizardPage2(QtWidgets.QWizardPage):
    def __init__(self):
        super(ProxyWizardPage2, self).__init__()

        Common.use_proxy = True
        translation = _translations(Common.translations_path, 'whonixsetup')
        self._ = translation.gettext
        self.steps = Common.wizard_steps

        self.proxies = ['-',
                        'SOCKS4',
                        'SOCKS5',
                        'HTTP / HTTPS']

        self.layout = QtWidgets.QVBoxLayout(self)
        self.label = QtWidgets.QLabel(self)
        self.layout.addWidget(self.label)

        self.groupBox = QtWidgets.QGroupBox(self)
        self.label_3 = QtWidgets.QLabel(self.groupBox)
        self.comboBox = QtWidgets.QComboBox(self.groupBox)
        self.label_2 = QtWidgets.QLabel(self.groupBox)
        self.label_5 = QtWidgets.QLabel(self.groupBox)
        self.label_6 = QtWidgets.QLabel(self.groupBox)
        self.lineEdit = QtWidgets.QLineEdit(self.groupBox)  # IP TODO: An inputmask() will make user more clear about what to input: https://doc.qt.io/qt-4.8/qlineedit.html#displayText-prop
        self.label_7 = QtWidgets.QLabel(self.groupBox)
        self.lineEdit_2 = QtWidgets.QLineEdit(self.groupBox)  # Port
        self.lineEdit_3 = QtWidgets.QLineEdit(self.groupBox)  # Username
        self.lineEdit_4 = QtWidgets.QLineEdit(self.groupBox)  # password
        self.lineEdit_4.setEchoMode(QLineEdit.Password)  # password mask
        self.label_8 = QtWidgets.QLabel(self.groupBox)
        self.label_4 = QtWidgets.QLabel(self.groupBox)
        self.pushButton = QtWidgets.QPushButton(self.groupBox)

        self.layout.addWidget(self.groupBox)
        self.setupUi()

    def setupUi(self):
        self.label.setMinimumSize(QtCore.QSize(16777215, 35))
        font = QtGui.QFont()
        font.setPointSize(11)
        font.setBold(True)
        font.setWeight(75)
        self.label.setFont(font)
        self.label.setText('   Local Proxy Configuration')

        self.groupBox.setMinimumSize(QtCore.QSize(16777215, 300))
        self.groupBox.setFlat(True)

        self.label_3.setGeometry(QtCore.QRect(10, 60, 106, 20))
        self.label_3.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_3.setText("Proxy type:")

        # Here we are going to implement the proxy type selection
        # Change it to larger so  that all options fit
        self.comboBox.setGeometry(QtCore.QRect(118, 58, 121, 27))
        for proxy in self.proxies:
            self.comboBox.addItem(proxy)

        self.label_2.setGeometry(QtCore.QRect(10, 30, 201, 16))
        self.label_2.setText("Enter the proxy settings.")

        self.label_5.setGeometry(QtCore.QRect(10, 101, 106, 20))
        self.label_5.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_5.setText("Address:")

        '''Username and Password options should be hide
        using "advance" button because it is not used rarely,
        according to recommendation from previous research.
        '''
        self.label_6.setGeometry(QtCore.QRect(10, 131, 106, 20))
        self.label_6.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_6.setText("Username:")

        self.label_7.setGeometry(QtCore.QRect(394, 101, 41, 20))
        self.label_7.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_7.setText("Port:")

        self.label_8.setGeometry(QtCore.QRect(280, 131, 70, 20))
        self.label_8.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_8.setText("Password:")


        ''' More instruction should be given as default.
        For example, 127.0.0.1.
        Other help may also be give in different ways:
        1. tooltip for each option
        2. option for users to configure well-known third party automatically (We can take foxyproxy's default setting as references.)
        '''
        self.lineEdit.setGeometry(QtCore.QRect(118, 98, 260, 25))
        self.lineEdit.setStyleSheet("background-color:white;")
        self.lineEdit.setPlaceholderText('IP address or hostname')
        self.lineEdit_2.setGeometry(QtCore.QRect(437, 98, 60, 25))
        self.lineEdit_2.setStyleSheet("background-color:white;")
        self.lineEdit_3.setGeometry(QtCore.QRect(118, 128, 150, 25))
        self.lineEdit_3.setStyleSheet("background-color:white;")
        self.lineEdit_3.setPlaceholderText('Optional')
        self.lineEdit_4.setGeometry(QtCore.QRect(352, 128, 145, 25))
        self.lineEdit_4.setStyleSheet("background-color:white;")
        self.lineEdit_4.setPlaceholderText('Optional')

        self.label_4.setGeometry(QtCore.QRect(10, 255, 500, 15))
        self.label_4.setText(Common.assistance)

        self.pushButton.setGeometry(QtCore.QRect(400, 200, 86, 25))
        self.pushButton.setText('&Help')
        self.pushButton.clicked.connect(self.show_help)


    # Q: Why there is no nextId function in original script? Unnecessary or Incomplete?
    # Q: Where is the nextId function called? It seems we can still go to next page without it.

    ''' The default_button and custom_button are not implemented in proxy setting now.
    The button can be used as well_known_proxy_setting auto-configuration or enter info manually by users
    Please uncomment it to use the function in the future.
    '''
    def nextId(self):
        # if self.default_button.isChecked():
        proxy_type = str(self.comboBox.currentText())
        if proxy_type.startswith('-'):
            # TODO: fix bug when messgeBox pop up
            #QMessageBox.about(self, "Title", "Message")
            use_proxy = False
            proxy_type = '-'
            return self.steps.index('proxy_wizard_page_2') # stay at the page until a proxy type is selected
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
        '''
        elif self.custom_button.isChecked():
            pass
        '''
        return self.steps.index('torrc_page')

    # TODO: Disable lineEdit_3 and lineEdit_4 which are username and password options when socks4 is selected.
    # Actvation signal: self.connection_page.censored.toggled.connect(self.set_next_button_state)
    #    self.lineEdit_3 = QtWidgets.QLineEdit(self.groupBox)  # Username
    #    self.lineEdit_4 = QtWidgets.QLineEdit(self.groupBox)  # Password TODO: password should be covered: https://doc.qt.io/qt-4.8/qlineedit.html#displayText-prop
    # called by button toggled signal.
    #def set_username_and_password_state(self, state):
    #    if state:
    #        self.button(QtWidgets.QWizard.NextButton).setEnabled(False)
    #    else:
    #        self.button(QtWidgets.QWizard.NextButton).setEnabled(True)

    # TODO: write a Proxy Configuration Help
    def show_help(self):
        reply = QtWidgets.QMessageBox(QtWidgets.QMessageBox.NoIcon, 'Proxy Configuration Help',
                                  '''<p><b>  Proxy Help</b></p>

<p>If you are unable to connect to the Tor network, it could be that your Internet Service
Provider (ISP) or another agency is blocking Tor.  Often, you can work around this problem
                                  by using Tor Bridges, which are unlisted relays that are more difficult to block. However, sometimes people may also use some third party censorship circumvention tools instead when all the Tor Bridges are not effective.</p>

<p>You may use the preconfigured, provided set of bridge addresses or you may obtain a
custom set of addresses by using one of these three methods:</p>

<blockquote>1.<b>Through the Web</b><br>
Use a web browser to visit https://bridges.torproject.org</blockquote>

<blockquote>2. <b>Through the Email Autoresponder</b><br>
Send email to bridges@torproject.org with the line 'get bridges' by itself in the body
of the message.  However, to make it harder for an attacker to learn a lot of bridge
addresses, you must send this request from one of the following email providers
(listed in order of preference):<br><br>
https://www.riseup.net, https://mail.google.com, or https://mail.yahoo.com</blockquote>

<blockquote>3. <b>Through the Help Desk</b><br>
As a last resort, you can request bridge addresses by sending a polite email
message to help@rt.torproject.org.  Please note that a person will need to respond
to each request.</blockquote>''', QtWidgets.QMessageBox.Ok)
        reply.exec_()


class TorrcPage(QtWidgets.QWizardPage):
    def __init__(self):
        super(TorrcPage, self).__init__()

        self.steps = Common.wizard_steps

        self.icon = QtWidgets.QLabel(self)
        self.text = QtWidgets.QTextBrowser(self)
        self.torrc = QtWidgets.QTextEdit(self)

        self.layout = QtWidgets.QGridLayout()
        self.setupUi()

    def setupUi(self):
        self.icon.setAlignment(QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.icon.setMinimumSize(50, 0)

        self.text.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.text.setAlignment(QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)

        # This is the QTextEdit that shows torrc files
        self.torrc.setEnabled(True)
        self.torrc.setMinimumSize(0, 185)
        self.torrc.setStyleSheet("background-color:white;")
        self.torrc.setReadOnly(True)
        # Allow long input appears in one line.
        self.torrc.setLineWrapColumnOrWidth(1800)
        self.torrc.setLineWrapMode(QtWidgets.QTextEdit.FixedPixelWidth)


        self.layout.addWidget(self.icon, 0, 0, 1, 1)
        self.layout.addWidget(self.text, 0, 1, 1, 2)
        self.layout.addWidget(self.torrc, 1, 1, 1, 1)
        self.setLayout(self.layout)

    def nextId(self):
        return self.steps.index('tor_status_page')



class TorStatusPage(QtWidgets.QWizardPage):
    def __init__(self):
        super(TorStatusPage, self).__init__()

        self.steps = Common.wizard_steps

        # self.icon = QtWidgets.QLabel(self)
        self.bootstrap_text = QtWidgets.QLabel(self)
        self.text = QtWidgets.QLabel(self)
        # self.torrc = QtWidgets.QPlainTextEdit(self)

        # Creating a progress bar
        self.bootstrap_progress = QtWidgets.QProgressBar(self)

        # Creating a Layout to add all the widgets
        self.layout = QtWidgets.QGridLayout()
        self.setupUi()

    def setupUi(self):
        # self.text.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.text.setWordWrap(True)
        self.text.setAlignment(QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.text.setMinimumSize(0, 290)

        # Setting the value limits of the progress bar
        self.bootstrap_progress.setMinimumSize(400, 0)
        self.bootstrap_progress.setMinimum(0)
        self.bootstrap_progress.setMaximum(100)
        self.bootstrap_progress.setVisible(False)

        # Adding the widgets
        self.layout.addWidget(self.text, 0, 1, 1, 2)
        self.layout.addWidget(self.bootstrap_progress, 1, 1, 1, 1)

        # Setting the layout as the main layout
        self.setLayout(self.layout)

app = QtWidgets.QApplication(sys.argv)



class AnonConnectionWizard(QtWidgets.QWizard):
    def __init__(self):
        super(AnonConnectionWizard, self).__init__()

        translation = _translations(Common.translations_path, 'whonixsetup')
        self._ = translation.gettext

        self.steps = Common.wizard_steps
        # The sequence of adding a page will also be the sequence the pages are shown in a wizard.
        self.connection_main_page = ConnectionMainPage()
        self.addPage(self.connection_main_page)

        self.bridge_wizard_page_1 = BridgesWizardPage1()
        self.addPage(self.bridge_wizard_page_1)
        self.bridge_wizard_page_2 = BridgesWizardPage2()
        self.addPage(self.bridge_wizard_page_2)

        self.proxy_wizard_page_1 = ProxyWizardPage1()
        self.addPage(self.proxy_wizard_page_1)
        self.proxy_wizard_page_2 = ProxyWizardPage2()
        self.addPage(self.proxy_wizard_page_2)
        
        self.torrc_page = TorrcPage()
        self.addPage(self.torrc_page)
        
        self.tor_status_page = TorStatusPage()
        self.addPage(self.tor_status_page)

        # self.bootstrap_thread = TorBootstrap(self)
        # self.bootstrap_thread.finished.connect(app.exit)
        # self.connect(self.bootstrap_thread, self.bootstrap_thread.signal, self.update_bootstrap)
        self.bridges = []
        self.proxy_type = ''
        self.tor_status = ''
        self.bootstrap_done = False

        ## Keep /etc/tor/anon_connection_wizard.torrc.tmp clear at start so that even if
        ## user clicked cancel button before making any changes,
        ## the anon_connection_wizard.torrc will not be polluted.
        if os.path.exists(Common.torrc_tmp_file_path):
            if os.path.exists('/etc/tor/anon-connection-wizard.torrc.orig'):
                shutil.copy('/etc/tor/anon-connection-wizard.torrc.orig', Common.torrc_tmp_file_path)
            else:
                print('Warning: /etc/tor/anon-connection-wizard.torrc.orig is missing.')

        self.setupUi()


    def setupUi(self):
        self.setWindowIcon(QtGui.QIcon("/usr/share/icons/anon-icon-pack/whonix.ico"))
        self.setWindowTitle('Anon Connection Wizard')
        self.resize(580, 400)

        ## TODO: hide the close button so that cancel button will be used when quit
        ## Otherwise try to connect the close button to cancel_button_clicked function
        # enable custom window hint
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.CustomizeWindowHint)
        # disable (but not hide) close button
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowCloseButtonHint)

        
        # signal-and-slot
        self.button(QtWidgets.QWizard.BackButton).clicked.connect(self.back_button_clicked)
        self.button(QtWidgets.QWizard.NextButton).clicked.connect(self.next_button_clicked)
        self.button(QtWidgets.QWizard.CancelButton).clicked.connect(self.cancel_button_clicked)
        
        self.button(QtWidgets.QWizard.BackButton).setVisible(False)  # Since this is the index page, no back_button is needed.
        self.button(QtWidgets.QWizard.BackButton).setEnabled(False)  # Since this is the index page, no back_button is needed.
        self.CancelButtonOnLeft
        self.button(QtWidgets.QWizard.CancelButton).setVisible(True)
        self.button(QtWidgets.QWizard.CancelButton).setEnabled(True)
        self.button(QtWidgets.QWizard.CancelButton).setText('Quit')
        #self.button(QtWidgets.QWizard.CancelButton).setFocus()
        self.exec_()


    def update_bootstrap(self, status):
        if status != 'timeout':
            bootstrap_phase = re.search(r'SUMMARY=(.*)', status).group(1)
            bootstrap_percent = int(re.match('.* PROGRESS=([0-9]+).*', status).group(1))
            if bootstrap_percent == 100:
                self.tor_status_page.text.setText('<p><b>Tor bootstrapping done</b></p>Bootstrap phase: {0}'.format(bootstrap_phase))
                self.bootstrap_done = True
            else:
                self.tor_status_page.text.setText('<p><b>Bootstrapping Tor...</b></p>Bootstrap phase: {0}'.format(bootstrap_phase))
            self.tor_status_page.bootstrap_progress.setValue(bootstrap_percent)
        else:
            self.bootstrap_timeout = True

    def cancel_button_clicked(self):
        ## sometimes the changes have been made to anon_connection_wizard.torrc but aborted
        if os.path.exists(Common.torrc_tmp_file_path):
            shutil.copy(Common.torrc_tmp_file_path , Common.torrc_file_path)

        try:
            if self.bootstrap_thread:
                self.bootstrap_thread.terminate()
        except AttributeError:
            pass

    def next_button_clicked(self):
        if self.currentId() == self.steps.index('connection_main_page'):
            self.resize(580, 400)
            self.button(QtWidgets.QWizard.CancelButton).setVisible(True)
            self.button(QtWidgets.QWizard.FinishButton).setVisible(False)
            #self.center()
            
            
        if self.currentId() == self.steps.index('torrc_page'):
            self.resize(580, 400)
            self.button(QtWidgets.QWizard.BackButton).setVisible(True)
            self.button(QtWidgets.QWizard.CancelButton).setVisible(True)
            self.button(QtWidgets.QWizard.FinishButton).setVisible(False)
            #self.center()

            ''' io() will wirte lines to /etc/torrc.d/anon_connection_wizard.torrc
            basing on user's selection in anon_connection_wizard
            '''
            io()
            
            ''' displace the torrc file and icon used on the page
            notice that anon_connection_wizard.torrc will not have line about DisableNetwork 0
            That line will be changed by tor_status module in /etc/torrc
            '''
            if not Common.disable_tor:
                #self.torrc_page.text.setText(self._('tor_enabled'))  # Q: how does this line work?
                self.torrc_page.text.setText('Tor will be enabled.')  # TODO: add more detailed instructions
                torrc_text = open(Common.torrc_file_path).read()
                self.torrc_page.torrc.setPlainText(torrc_text)
                self.torrc_page.icon.setPixmap(QtGui.QPixmap( \
                    '/usr/share/icons/oxygen/48x48/status/task-complete.png'))
            else:
                #self.torrc_page.text.setText(self._('tor_disabled'))
                self.torrc_page.text.setText('Tor will be disabled.')
                torrc_text = open(Common.torrc_file_path).read()
                self.torrc_page.torrc.setPlainText(torrc_text)
                self.torrc_page.icon.setPixmap(QtGui.QPixmap( \
                    '/usr/share/icons/oxygen/48x48/status/task-attention.png'))

        if self.currentId() == self.steps.index('tor_status_page'):
            self.tor_status_page.text.setText('')  # This will clear the text left by different Tor status statement
            if self.tor_status == 'tor_enabled' or self.tor_status == 'tor_already_enabled':
                self.tor_status_page.bootstrap_progress.setVisible(True)

            self.button(QtWidgets.QWizard.BackButton).setVisible(True)
            self.button(QtWidgets.QWizard.CancelButton).setVisible(True)
            self.button(QtWidgets.QWizard.FinishButton).setVisible(False)

            '''Arranging different tor_status_page according to the value of disable_tor.'''
            if not Common.disable_tor:
                self.tor_status = tor_status.set_enabled()
                self.tor_status_page.text.setText('')  # This will clear the text left by different Tor status statement
                if self.tor_status == 'tor_enabled' or self.tor_status == 'tor_already_enabled':
                    self.tor_status_page.bootstrap_progress.setVisible(True)
                    self.bootstrap_thread = TorBootstrap(self)
                    self.bootstrap_thread.signal.connect(self.update_bootstrap)
                    self.bootstrap_thread.finished.connect(self.show_finish_button)
                    self.bootstrap_thread.start()
                else:
                    pass
            else:
                self.tor_status = tor_status.set_disabled()
                self.tor_status_page.bootstrap_progress.setVisible(False)
                self.tor_status_page.text.setText('<b>Tor is disabled.</b> You will not be able to use any \
                                                   network facing application.<p> If you shut down the gateway \
                                                   now, this wizard will be run automatically next time you boot. \
                                                   </p><p>You can run it at any moment using <i>Anon Connection Wizard</i> \
                                                   from your application launcher, or from a terminal:<blockquote> \
                                                   <code>kdesudo anon-connection-wizard</code></blockquote> \
                                                   or press the Back button and select another option.')
                self.show_finish_button()

    def back_button_clicked(self):
        try:
            if self.bootstrap_thread:
                self.bootstrap_thread.terminate()
        except AttributeError:
            pass

        if self.currentId() == self.steps.index('connection_main_page'):
            Common.use_bridges = False
            Common.use_proxy = False
            shutil.copy('/etc/tor/anon-connection-wizard.torrc.orig', Common.torrc_file_path)
            
            self.bootstrap_done = False
            self.button(QtWidgets.QWizard.FinishButton).setVisible(False)
            self.button(QtWidgets.QWizard.CancelButton).setVisible(True)

        if self.currentId() == self.steps.index('proxy_wizard_page_1'):
            self.bootstrap_done = False
            self.button(QtWidgets.QWizard.FinishButton).setVisible(False)
            self.button(QtWidgets.QWizard.CancelButton).setVisible(True)

    def show_finish_button(self):
        if self.bootstrap_done or Common.disable_tor:
            self.button(QtWidgets.QWizard.CancelButton).setVisible(False)
            self.button(QtWidgets.QWizard.FinishButton).setVisible(True)
            self.button(QtWidgets.QWizard.FinishButton).setFocus()


class TorBootstrap(QtCore.QThread):
    signal = QtCore.pyqtSignal(str)
    def __init__(self, main):
        from stem.connection import connect
        #super(TorBootstrap, self).__init__(main)
        QtCore.QThread.__init__(self, parent=None)
        self.controller = connect()
        if not self.controller:
            print("no tor control connected!!!")
        #self.signal = QtCore.SIGNAL("signal")
        self.previous_status = ''
        self.bootstrap_percent = 0
        #self.is_running = False

    def run(self):
        #self.is_running = True
        while self.bootstrap_percent < 100:
            bootstrap_status = self.controller.get_info("status/bootstrap-phase")
            self.bootstrap_percent = int(re.match('.* PROGRESS=([0-9]+).*', bootstrap_status).group(1))
            if bootstrap_status != self.previous_status:
                sys.stdout.write('{0}\n'.format(bootstrap_status))
                sys.stdout.flush()
                self.previous_status = bootstrap_status
                self.signal.emit(bootstrap_status)
            time.sleep(0.2)

''' 
'''
def io():
            ## Get a fresh anon-connection-wizard.torrc
            if not os.path.exists('/etc/torrc.d'):
                os.makedirs('/etc/torrc.d')
            if os.path.exists(Common.torrc_file_path):
                # TODO: torrc.tmp serves as a backup of users' previous setting
                # we need discuss if this file is a good design
                # we also need to know where should we put it.
                shutil.copy(Common.torrc_file_path, Common.torrc_tmp_file_path)
            else:
                pass

            # TODO: we may add how to open anon_connection_wizard in the instruction in .orig
            if os.path.exists('/etc/tor/anon-connection-wizard.torrc.orig'):
                shutil.copy('/etc/tor/anon-connection-wizard.torrc.orig', Common.torrc_file_path)
            else:
                print('Warning: /etc/tor/anon-connection-wizard.torrc.orig is missing.')

            ''' This part is the IO to torrc for bridges settings.
            Related official docs: https://www.torproject.org/docs/tor-manual.html.en
            '''
            if Common.use_bridges:
                with open(Common.torrc_file_path, 'a') as f:
                    f.write('UseBridges 1\n')
                    if Common.use_default_bridge:
                        if Common.bridge_type == 'obfs3':
                            f.write('ClientTransportPlugin obfs2,obfs3 exec /usr/bin/obfsproxy managed\n')
                        elif Common.bridge_type == 'scramblesuit':
                            f.write('ClientTransportPlugin obfs2,obfs3,scramblesuit exec /usr/bin/obfsproxy managed\n')
                        elif Common.bridge_type == 'obfs4':
                            f.write('ClientTransportPlugin obfs4 exec /usr/bin/obfs4proxy\n')
                            # More types of bridges will be availble once Whonix support them: meek, flashproxy
                        #elif Common.bridge_type == '':
                        bridges = json.loads(open(Common.bridges_default_path).read())  # default bridges will be loaded, however, what does the variable  bridges do? A: for bridge in bridges
                        # Q: What does json.load do?
                        for bridge in bridges['bridges'][Common.bridge_type]:  # What does this line mean? A: The bridges are more like a multilayer-dictionary
                            f.write('Bridge {0}\n'.format(bridge))  # This is the format to configure a bridge in torrc
                    else:  # Use custom bridges
                        # TODO: we should preserve the custom bridge setting for the next time use.
                        # TODO: Unfinished for different types of bridges:
                        if Common.bridge_custom.startswith('obfs4'):
                            f.write('ClientTransportPlugin obfs4 exec /usr/bin/obfs4proxy\n')
                        elif Common.bridge_custom.startswith('obfs3'):
                            f.write('ClientTransportPlugin obfs2,obfs3 exec /usr/bin/obfsproxy managed\n')
                        elif Common.bridge_custom.startswith('fte'):
                            f.write('ClientTransportPlugin fte exec /usr/bin/fteproxy --managed\n')
                        elif Common.bridge_custom.startswith('meek-amazon'):
                            pass  # Wait to be implemented in Whonix.
                        elif Common.bridge_custom.startswith('meek-azure'):
                            pass

                        # Write the specific bridge address, port, cert etc.
                        bridge_custom_list = Common.bridge_custom.split('\n')
                        for bridge in bridge_custom_list:
                            f.write('Bridge {0}\n'.format(bridge))


            ''' The part is the IO to torrc for proxy settings.
            Related official docs: https://www.torproject.org/docs/tor-manual.html.en
            '''
            if Common.use_proxy:
                with open(Common.torrc_file_path, 'a') as f:
                    # TODO: Notice that if SOCKS4 is selected, the proxy username and password inputLine should be disabled
                    # This is because SOCKS4 does not support that.
                    if Common.proxy_type == 'HTTP/HTTPS':
                        f.write('HTTPSProxy {0}:{1}\n'.format(Common.proxy_ip, Common.proxy_port))
                        if (Common.proxy_username != ''):  # Q: It seems there is no need to check password because username is essential, not password, right?
                            f.write('HTTPSProxyAuthenticator {0}:{1}\n'.format(Common.proxy_username, Common.proxy_password))
                    elif Common.proxy_type == 'SOCKS4':
                        f.write('Socks4Proxy {0}:{1}\n'.format(Common.proxy_ip, Common.proxy_port))
                    elif Common.proxy_type == 'SOCKS5':
                        f.write('Socks5Proxy {0}:{1}\n'.format(Common.proxy_ip, Common.proxy_port))
                        if (Common.proxy_username != ''):
                            f.write('Socks5ProxyUsername {0}\n'.format(Common.proxy_username))
                            f.write('Socks5ProxyPassword {0}\n'.format(Common.proxy_password))

                    ''' TODO: Another feature can be implemented in the future is auto-configure for well-known third party proxy-based censorship circumvention tools, like Lantern.
                    Uncomment all the fragments to enable it.
                    '''
                    # proxies = json.loads(open(Common.well_known_proxy_setting_default_path).read())  # default bridges will be loaded, however, what does the variable  bridges do? A: for bridge in bridges
                    # for proxy in proxies['proxies'][Common.well_known_proxy_setting]:
                    #    f.write('{0}\n'.format(proxy))

def main():
    # Available styles: "windows", "motif", "cde", "sgi", "plastique" and "cleanlooks"
    # TODO: use customized css instead. Take Tor Launcher's css as a reference
    QtWidgets.QApplication.setStyle('cleanlooks')
    
    # root check.
    if os.getuid() != 0:
        print('ERROR: This must be run as root!\nUse "kdesudo".')
        not_root = gui_message(Common.translations_path, 'not_root')
        sys.exit(1)
        
    wizard = AnonConnectionWizard()

    sys.exit(0)

if __name__ == "__main__":
    main()
