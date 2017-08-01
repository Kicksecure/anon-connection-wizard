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
import tempfile

from guimessages.translations import _translations
from guimessages.guimessage import gui_message

from anon_connection_wizard import tor_status
from anon_connection_wizard import repair_torrc

class Common:
    '''
    Variables and constants used through all the classes
    '''
    translations_path = '/usr/share/translations/whonix_setup.yaml'
    torrc_file_path = '/etc/torrc.d/anon_connection_wizard.torrc'
    torrc_tmp_file_path = ''
    bridges_default_path = '/usr/share/anon-connection-wizard/bridges_default'
    # well_known_proxy_setting_default_path = '/usr/share/anon-connection-wizard/well_known_proxy_settings'
    
    control_cookie_path = '/run/tor/control.authcookie'
    control_socket_path = '/run/tor/control'
    
    use_bridges = False
    use_default_bridge = True
    bridge_type = 'obfs4 (recommended)'  # defualt value is 'obfs4 (recommended)', but it does not affect if obsf4 is used or not
    bridge_custom = ''  # the bridges info lines
    
    use_proxy = False
    proxy_type = 'HTTP / HTTPS'  # defualt is '-', not blank
    proxy_ip = ''
    proxy_port = ''
    proxy_username = ''
    proxy_password = ''

    disable_tor = False

    ''' The following is command lines availble to be added to .torrc,
    since they are used more than once in the code, 
    it is easier for later maintainance of the code to write them all here and refer them when used
    Notice that:
    1. they do not include '\n' 
    2. the ' ' appended at last should not be eliminate
    '''
    command_useBridges = 'UseBridges 1'
    command_use_custom_bridge = '# Custom Bridge is used:'
    command_obfs3 = 'ClientTransportPlugin obfs2,obfs3 exec /usr/bin/obfsproxy managed'
    command_obfs4 = 'ClientTransportPlugin obfs4 exec /usr/bin/obfs4proxy'
    command_fte = 'ClientTransportPlugin fte exec /usr/bin/fteproxy --managed'
    command_scramblesuit = 'ClientTransportPlugin obfs2,obfs3,scramblesuit exec /usr/bin/obfsproxy managed'
    command_bridgeInfo = 'Bridge '
    
    command_http = 'HTTPSProxy '
    command_httpAuth = 'HTTPSProxyAuthenticator'
    command_sock4 = 'Socks4Proxy '
    command_sock5 = 'Socks5Proxy '
    command_sock5Username = 'Socks5ProxyUsername'
    command_sock5Password = 'Socks5ProxyPassword'

    ''' The following is a variable serves as a flag to work around the bug
    that a "blank IP/Port" messgae show up even when switching from proxy_wizard_page_1
    to proxy_wizard_page_2.
    '''
    to_proxy_page_2 = True
    from_bridge_page_1 = True

    ''' The following is the fonts used throughout the anon_connection_wizard.
    Since we need the consistence in fonts settings to create a better UI,
    '''

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


    
    if not os.path.exists('/var/cache/whonix-setup-wizard/status-files'):
        os.makedirs('/var/cache/whonix-setup-wizard/status-files')

    if not os.path.exists('/var/cache/whonix-setup-wizard/status-files/whonix_connection.done'):
        ## "not whonix_connection.done" is required once at first run to get a copy of the original torrc.
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

    control_cookie_path = '/run/tor/control.authcookie'
    control_socket_path = '/run/tor/control'



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

        font_description_minor = Common.font_description_minor
        font_description_main = Common.font_description_main
        font_option = Common.font_option
        
        self.label.setGeometry(QtCore.QRect(10, 20, 530, 41))
        self.label.setWordWrap(True)
        self.label.setText('Before you connect to the Tor network, you need to provide information about this computer\'s Internet connection.')
        self.label.setFont(font_description_minor)


        self.label_2.setGeometry(QtCore.QRect(10, 65, 431, 21))
        self.label_2.setFont(font_description_main)
        self.label_2.setText('Which of the following best describes your situation?')

        self.label_3 = QtWidgets.QLabel(self.groupBox)
        self.label_3.setGeometry(QtCore.QRect(10, 90, 321, 41))
        self.label_3.setWordWrap(True)
        self.label_3.setText('I would like to connect directly to the Tor network. This will work in most situations.')
        self.label_3.setFont(font_description_minor)

        self.pushButton_1.setGeometry(QtCore.QRect(20, 133, 110, 26))
        self.pushButton_2.setGeometry(QtCore.QRect(20, 213, 110, 26))
        self.pushButton_3.setGeometry(QtCore.QRect(20, 288, 110, 26))
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

        if Common.use_bridges or Common.use_proxy:
            self.pushButton_2.setChecked(True)
        else:
            self.pushButton_1.setChecked(True)


    def nextId(self):
        if self.pushButton_1.isChecked():
            # clear all setting
            Common.disable_tor = False
            Common.use_bridges = False
            Common.use_proxy = False
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
        self.pushButton = QtWidgets.QPushButton(self.group_box)
        self.layout.addWidget(self.group_box)

        self.setupUi()

    def setupUi(self):
        self.label.setMinimumSize(QtCore.QSize(16777215, 35))

        font_title = Common.font_title
        font_description_main = Common.font_description_main
        font_description_minor = Common.font_description_minor
        font_option = Common.font_option
        
        self.label.setFont(font_title)
        self.label.setText('   Tor Bridges Configuration')

        self.label_2.setMaximumSize(QtCore.QSize(16777215, 50))
        self.label_2.setFont(font_description_main)
        self.label_2.setWordWrap(True)
        #self.label_2.setText('Does your Internet Service Provider (ISP) block or otherwise censor connections to the Tor network?')
        self.label_2.setText('Do you want to configure Tor bridges?')

        self.group_box.setMinimumSize(QtCore.QSize(16777215, 244))
        self.group_box.setFlat(True)

        self.yes_button.setGeometry(QtCore.QRect(25, 30, 550, 30))
        self.yes_button.setText('Yes. I need Tor bridges to bypass the Tor censorship.')
        self.yes_button.setFont(font_option)
        
        self.no_button_1.setGeometry(QtCore.QRect(25, 60, 550, 30))
        #self.no_button_1.setText('No. My ISP does not censor my connections to the Tor network or I will use other censorship circumvention methods instead.')
        self.no_button_1.setText('No.')
        self.no_button_1.setFont(font_option)
        
        #self.no_button_2.setGeometry(QtCore.QRect(25, 50, 550, 30))
        #self.no_button_2.setText('No. I will use some third party censorship circumvention tools instead.')

        ## This is an example of how to adjust UI according to Common.value
        ## which are changed according to .torrc at the start of anon_connection_wizard
        if Common.use_bridges:
            self.yes_button.setChecked(True)
        else:
            self.no_button_1.setChecked(True)

        # self.label_3.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.label_3.setGeometry(10, 110, 500, 160)
        self.label_3.setTextFormat(QtCore.Qt.RichText)
        self.label_3.setWordWrap(True)
        self.label_3.setText('Tor bridges are unlisted relays that may be able to help you\
        bypass the Tor censorship conducted by your Internet Service Provider (ISP).')
        self.label_3.setFont(font_description_minor)

        self.label_4.setGeometry(10, 220, 500, 15)
        self.label_4.setText(Common.assistance)
        self.label_4.setFont(font_description_minor)

        self.pushButton.setEnabled(True)
        self.pushButton.setGeometry(QtCore.QRect(300, 105, 150, 25))
        self.pushButton.setText('&How to decide?')
        self.pushButton.clicked.connect(self.show_help)


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

    def show_help(self):
        reply = QtWidgets.QMessageBox(QtWidgets.QMessageBox.NoIcon, 'Censorship Circumvention Help',
                                  '''<p><b>  Censorship Circumvention Help</b></p>

<p>If you are unable to connect to the Tor network, it could be that your Internet Service
Provider (ISP) or another agency is blocking Tor.  Often, you can work around this problem
by using Tor Bridges, which are unlisted relays that are more difficult to block.</p>


<p>Tor bridges are the recommended way to circumvent the Tor censorship. You should always take it as the first option to help you pypass the Tor censorship. However, if you are living in a heavily censored area where all the Tor bridges are invalid, you may need to use some third-party censorship circumvention tools to help you instead. In such a case, you should choose not using Tor bridges to help you bypass the Tor censorship.</p>

<p> Using a third-party censorship circumvention tool may harm you security and/or anonimity. However, in case you do need it, the following is an instruction on how to connect to the Tor network using different censorship circumvention tools:</p>

<blockquote><b>1. VPN</b><br>
1. Establish your connection to the VPN server; 2. Hit the "back" buton on this page, going to the first page; 3. Hit the "Connect" button on the first page.</blockquote>

<blockquote><b>2. HTTP/Socks Proxy</b><br>
1. Choose not using Tor bridges in this page; 2. Hit the "next" buton on this page, going the Proxy Configuration page; 3. Configure a proxy.</blockquote>

<blockquote><b>3. Specialized Tool </b><br>
1. Figure out the listening port of the tool, including the port protocal and the port number; 2. Choose not using Tor bridges in this page; 3. Hit the "next" buton on this page, going the Proxy Configuration page; 4. Configure a proxy.</blockquote>
''', QtWidgets.QMessageBox.Ok)
        reply.exec_()



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

        '''
        self.groupBox_default = QtWidgets.QGroupBox(self)
        self.groupBox_custom = QtWidgets.QGroupBox(self)
        '''
        
        self.default_button = QtWidgets.QRadioButton(self.groupBox)
        self.custom_button = QtWidgets.QRadioButton(self.groupBox)

        self.label_3 = QtWidgets.QLabel(self.groupBox)
        self.comboBox = QtWidgets.QComboBox(self.groupBox)
        
        self.label_4 = QtWidgets.QLabel(self.groupBox)
        self.custom_bridges = QtWidgets.QTextEdit(self.groupBox)  # QTextEdit box for bridges.
        self.pushButton = QtWidgets.QPushButton(self.groupBox)

        self.label_5 = QtWidgets.QLabel(self.groupBox)

        self.layout.addWidget(self.groupBox)

        '''
        self.layout.addWidget(self.groupBox_default)
        self.layout.addWidget(self.groupBox_custom)
        '''
        
        self.setupUi()

    def setupUi(self):
        self.label.setMinimumSize(QtCore.QSize(16777215, 35))

        font_title = Common.font_title
        font_description_main = Common.font_description_main
        font_description_minor = Common.font_description_minor
        font_option = Common.font_option

        self.label.setText('   Tor Bridges Configuration')
        self.label.setFont(font_title)


        self.label_2.setMaximumSize(QtCore.QSize(16777215, 50))
        self.label_2.setFont(font_description_main)
        self.label_2.setWordWrap(True)
        self.label_2.setText('You may use the provided set of bridges or you may obtain and enter a custom set of bridges.')

        self.groupBox.setMinimumSize(QtCore.QSize(16777215, 243))
        self.groupBox.setFlat(True)

        '''
        self.groupBox_default.setMinimumSize(QtCore.QSize(16777215, 243))
        self.groupBox_default.setFlat(True)
        self.groupBox_default.setVisible(True)

        self.groupBox_custom.setMinimumSize(QtCore.QSize(16777215, 243))
        self.groupBox_custom.setFlat(True)
        self.groupBox_custom.setVisible(False)
        '''

        
        self.default_button.setGeometry(QtCore.QRect(18, 25, 500, 24))
        self.default_button.setText('Connect with provided bridges')
        self.default_button.setFont(font_description_minor)

        self.custom_button.setGeometry(QtCore.QRect(18, 82, 500, 25))
        self.custom_button.setText('Enter custom bridges')
        self.custom_button.setFont(font_description_minor)

        if Common.use_default_bridge:
            self.default_button.setChecked(True)
        else:
            self.custom_button.setChecked(True)

        # This will emit a signal every time default_button is toggled
        self.default_button.toggled.connect(self.show_default_bridge)

        self.label_3.setGeometry(QtCore.QRect(40, 52, 106, 20))
        self.label_3.setText('Transport type:')
        self.label_3.setFont(font_description_minor)

        # This is the how to make a comboBox. The variable bridges is defined above.
        # The proxy type selection in ProxyWizardPage2 can also use this method.
        self.comboBox.setGeometry(QtCore.QRect(140, 49, 181, 27))
        for bridge in self.bridges:
            self.comboBox.addItem(bridge)
            
        # The default value is adjust according to Common.bridge_type
        if Common.use_default_bridge:
            self.comboBox.setCurrentIndex(self.bridges.index(Common.bridge_type))

        self.label_4.setEnabled(False)
        self.label_4.setVisible(False)
        self.label_4.setGeometry(QtCore.QRect(38, 105, 300, 20))
        self.label_4.setText('Enter one or more bridge relay (one per line).')

        # TODO: The boolean value of this should be the same with self.custom_button.isChecked() Q: How to do it dynamically? A: signal-and-slot.
        # Notice that this feature is not in Tor launcher, this can be an improvement which also benefits upstream.
        # TODO: Make this QTextEdit support syntax to make it even more clear to users what should be input: https://doc.qt.io/archives/qq/qq21-syntaxhighlighter.html
        self.custom_bridges.setEnabled(True)
        self.custom_bridges.setVisible(False)
        self.custom_bridges.setGeometry(QtCore.QRect(38, 125, 500, 76))
        self.custom_bridges.setStyleSheet("background-color:white;")
        # Allow long input appears in one line.
        self.custom_bridges.setLineWrapColumnOrWidth(1800)
        self.custom_bridges.setLineWrapMode(QtWidgets.QTextEdit.FixedPixelWidth)
        
        if not Common.use_default_bridge:
            self.custom_bridges.setText(Common.bridge_custom)  # adjust the line according to value in Common

        
        # TODO: The next statement can not be used yet, this is because the QTextEdit does not supprot setPlaceholderText.
        # More functions need to be added to implement that: https://doc.qt.io/archives/qq/qq21-syntaxhighlighter.html
        # self.custom_bridges.setPlaceholderText('type address:port')

        self.pushButton.setEnabled(True)
        self.pushButton.setVisible(False)
        self.pushButton.setGeometry(QtCore.QRect(360, 80, 150, 25))
        self.pushButton.setText('&How to get Bridges?')
        self.pushButton.clicked.connect(self.show_help)

        self.label_5.setVisible(True)
        self.label_5.setGeometry(10, 220, 500, 15)
        self.label_5.setText(Common.assistance)
        self.label_5.setFont(font_description_minor)

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

            return self.steps.index('proxy_wizard_page_1')

        elif self.custom_button.isChecked():
            Common.bridge_custom = str(self.custom_bridges.toPlainText())
            Common.use_default_bridge = False

            if Common.bridge_custom == '':
                return self.steps.index('bridge_wizard_page_2') # stay at the page until a bridge is given'''
            else:
                return self.steps.index('proxy_wizard_page_1')



    def show_help(self):
        reply = QtWidgets.QMessageBox(QtWidgets.QMessageBox.NoIcon, 'Bridges Configuration Help',
                                  '''<p><b>  Bridge Relay Help</b></p>

<p>If you are unable to connect to the Tor network, it could be that your Internet Service
Provider (ISP) or another agency is blocking Tor.  Often, you can work around this problem
by using Tor Bridges, which are unlisted relays that are more difficult to block.</p>

<p>You may use the preconfigured, provided set of bridge addresses or you may obtain a
custom set of addresses by using one of these three methods:</p>

<blockquote><b>1. Through the Web</b><br>
Use a web browser to visit https://bridges.torproject.org/options</blockquote>

<blockquote><b>2. Through the Email Autoresponder</b><br>
Send email to bridges@torproject.org with the line 'get bridges' by itself in the body
of the message.  However, to make it harder for an attacker to learn a lot of bridge
addresses, you must send this request from one of the following email providers
(listed in order of preference):<br><br>
https://www.riseup.net, https://mail.google.com, or https://mail.yahoo.com</blockquote>

<blockquote><b>3. Through the Help Desk</b><br>
As a last resort, you can request bridge addresses by sending a polite email
message to help@rt.torproject.org.  Please note that a person will need to respond
to each request.</blockquote>''', QtWidgets.QMessageBox.Ok)
        reply.exec_()

    def show_default_bridge(self, default_button_checked):
        if default_button_checked:
            self.label_3.setVisible(True)
            self.comboBox.setVisible(True)

            self.label_4.setVisible(False)
            self.custom_bridges.setVisible(False)
            self.pushButton.setVisible(False)
        else:
            self.label_3.setVisible(False)
            self.comboBox.setVisible(False)

            self.label_4.setVisible(True)
            self.custom_bridges.setVisible(True)
            self.pushButton.setVisible(True)



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
        font_title = Common.font_title
        font_description_main = Common.font_description_main
        font_description_minor = Common.font_description_minor
        font_option = Common.font_option

        self.label.setMinimumSize(QtCore.QSize(16777215, 35))

        self.label.setText('   Local Proxy Configuration')
        self.label.setFont(font_title)

        self.label_2.setMaximumSize(QtCore.QSize(16777215, 50))
        self.label_2.setWordWrap(True)
        self.label_2.setText('Does this computer need to use a local proxy to access the Internet?')
        self.label_2.setFont(font_description_main)


        self.group_box.setMinimumSize(QtCore.QSize(16777215, 250))
        self.group_box.setFlat(True)
        self.yes_button.setGeometry(QtCore.QRect(25, 30, 350, 21))
        self.yes_button.setText('Yes.')
        self.yes_button.setFont(font_option)
        self.no_button.setGeometry(QtCore.QRect(25, 55, 350, 21))
        self.no_button.setText('No.')
        self.no_button.setChecked(True)
        self.no_button.setFont(font_option)

        if Common.use_proxy:
            self.yes_button.setChecked(True)
        else:
            self.no_button.setChecked(True)


        # self.label_3.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.label_3.setGeometry(10, 75, 520, 60)
        self.label_3.setTextFormat(QtCore.Qt.RichText)
        self.label_3.setWordWrap(True)
        self.label_3.setText('If you are not sure how to answer this question, look at the Internet \
                              settings in your host browser to see whether it is configured to use \
                              a local proxy.')
        self.label_3.setFont(font_description_minor)

        self.label_4.setGeometry(10, 265, 500, 15)
        self.label_4.setText(Common.assistance)
        self.label_4.setFont(font_description_minor)

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

        self.proxies = [#'-',
            'HTTP / HTTPS',
            'SOCKS4',
            'SOCKS5'
        ]

        self.layout = QtWidgets.QVBoxLayout(self)
        self.label = QtWidgets.QLabel(self)
        self.layout.addWidget(self.label)

        self.checkBox = QtWidgets.QCheckBox(self)  # enable proxy checkBox

        self.groupBox = QtWidgets.QGroupBox(self)
        
        
        self.label_2 = QtWidgets.QLabel(self.groupBox)  # instructions
        self.label_3 = QtWidgets.QLabel(self.groupBox)  # Proxy type lable
        self.comboBox = QtWidgets.QComboBox(self.groupBox) # Proxy type comboBox
        self.label_4 = QtWidgets.QLabel(self.groupBox)  # assistance info
        self.label_5 = QtWidgets.QLabel(self.groupBox)  # Address label
        self.label_6 = QtWidgets.QLabel(self.groupBox)  # username lable
        self.label_7 = QtWidgets.QLabel(self.groupBox)  # Port label
        self.label_8 = QtWidgets.QLabel(self.groupBox)  # password label

        self.lineEdit = QtWidgets.QLineEdit(self.groupBox)  # IP TODO: An inputmask() will make user more clear about what to input: https://doc.qt.io/qt-4.8/qlineedit.html#displayText-prop
        self.lineEdit_2 = QtWidgets.QLineEdit(self.groupBox)  # Port input
        self.lineEdit_3 = QtWidgets.QLineEdit(self.groupBox)  # Username input
        self.lineEdit_4 = QtWidgets.QLineEdit(self.groupBox)  # password input
        self.lineEdit_4.setEchoMode(QLineEdit.Password)  # password mask
        self.pushButton = QtWidgets.QPushButton(self.groupBox)

        self.layout.addWidget(self.groupBox)
        self.setupUi()

    def setupUi(self):
        self.label.setMinimumSize(QtCore.QSize(16777215, 35))

        font_title = Common.font_title
        font_description_main = Common.font_description_main
        font_description_minor = Common.font_description_minor
        font_option = Common.font_option


        self.label.setText('   Local Proxy Configuration')
        self.label.setFont(font_title)

        self.checkBox.stateChanged.connect(self.enable_proxy)
        self.checkBox.setText("Use Proxy")
        self.checkBox.setChecked(True)
        self.checkBox.setGeometry(QtCore.QRect(30, 40, 106, 20))
        
        self.comboBox.currentIndexChanged[str].connect(self.option_changed)
        '''
        toggled.connect(self.set_next_button_state)
        self.connection_page.use_proxy.toggled.connect(self.set_next_button_state)
        self.exec_()
        '''




        self.groupBox.setMinimumSize(QtCore.QSize(16777215, 300))
        self.groupBox.setFlat(True)

        self.label_3.setGeometry(QtCore.QRect(10, 60, 106, 20))
        self.label_3.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_3.setText("Proxy type: ")
        self.label_3.setFont(font_description_minor)

        # Here we are going to implement the proxy type selection
        # Change it to larger so  that all options fit
        self.comboBox.setGeometry(QtCore.QRect(118, 58, 121, 27))
        for proxy in self.proxies:
            self.comboBox.addItem(proxy)

        # The default value is adjust according to Common.proxy_type
        if Common.use_proxy:
            self.comboBox.setCurrentIndex(self.proxies.index(Common.proxy_type))


        self.label_2.setGeometry(QtCore.QRect(10, 30, 201, 16))
        self.label_2.setText("Enter the proxy settings.")
        self.label_2.setFont(font_description_minor)

        self.label_5.setGeometry(QtCore.QRect(10, 101, 106, 20))
        self.label_5.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_5.setText("Address: ")
        self.label_5.setFont(font_description_minor)

        '''Username and Password options should be hide
        using "advance" button because it is not used rarely,
        according to recommendation from previous research.
        '''
        self.label_6.setGeometry(QtCore.QRect(10, 131, 106, 20))
        self.label_6.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_6.setText("Username: ")
        self.label_6.setFont(font_description_minor)

        self.label_7.setGeometry(QtCore.QRect(394, 101, 41, 20))
        self.label_7.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_7.setText("Port: ")
        self.label_7.setFont(font_description_minor)

        self.label_8.setGeometry(QtCore.QRect(280, 131, 70, 20))
        self.label_8.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_8.setText("Password: ")
        self.label_8.setFont(font_description_minor)


        ''' More instruction should be given as default.
        For example, 127.0.0.1.
        Other help may also be give in different ways:
        1. tooltip for each option
        2. option for users to configure well-known third party automatically (We can take foxyproxy's default setting as references.)
        '''
        self.lineEdit.setGeometry(QtCore.QRect(118, 98, 260, 25))
        self.lineEdit.setStyleSheet("background-color:white;")
        self.lineEdit.setPlaceholderText('Example: 127.0.0.1')
        self.lineEdit.setText(Common.proxy_ip)  # TODO: investigate why it does not work
        # TODO: may exchange the sequence of setText and setPlaceholderText
        
        self.lineEdit_2.setGeometry(QtCore.QRect(437, 98, 60, 25))
        self.lineEdit_2.setStyleSheet("background-color:white;")
        self.lineEdit_2.setPlaceholderText('1-65535')
        self.lineEdit_2.setText(Common.proxy_port)
        
        self.lineEdit_3.setGeometry(QtCore.QRect(118, 128, 150, 25))
        self.lineEdit_3.setStyleSheet("background-color:white;")
        self.lineEdit_3.setPlaceholderText('Optional')
        self.lineEdit_3.setText(Common.proxy_username)
        
        self.lineEdit_4.setGeometry(QtCore.QRect(352, 128, 145, 25))
        self.lineEdit_4.setStyleSheet("background-color:white;")
        self.lineEdit_4.setPlaceholderText('Optional')
        self.lineEdit_4.setText(Common.proxy_password)

        self.label_4.setGeometry(QtCore.QRect(10, 255, 500, 15))
        self.label_4.setText(Common.assistance)
        self.label_4.setFont(font_description_minor)

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
        if self.lineEdit.text() == '' or self.lineEdit_2.text() == '':
            return self.steps.index('proxy_wizard_page_2') # stay at the page until a proxy type is selected'''

        # if self.default_button.isChecked():
        proxy_type = str(self.comboBox.currentText())
        '''
        if proxy_type.startswith('-'):
            # TODO: fix bug when messgeBox pop up
            #QMessageBox.about(self, "Title", "Message")
            use_proxy = False
            proxy_type = '-'
            return self.steps.index('proxy_wizard_page_2') # stay at the page until a proxy type is selected'''

        
        
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
                                  <p>In some situiations, you may want to transfer your traffic through a proxy server before connecting to the Tor network. For example, if you are trying to use a third-party censorship circumvention tool to bypass the Tor censorship, you need to configure Tor to connect to the listening port of that circumvention tools. </p>

<p> The following is a brief introduction on what each blank means and how you may find the proper input value:</p>

<blockquote><b>1. Proxy Type</b><br>
                                  The proxy type is protocal you use to communicate with the proxy server. Since there are only three options, you can try all of them to see which one works.</blockquote>

<blockquote><b>2. Proxy IP/hostname</b><br>
You have to know the port number you are trying to connect to. If you are trying to connect to a local proxy, you should try 127.0.0.1 since it means localhost.</blockquote>

<blockquote><b>3. Proxy Port number</b><br>
You have to know the port number you are trying to connect to. It should be a positive integer from 1 to 65535. If you are trying to find the listening port number of a well-known censorship circumvention tool, you may simply search it online.</blockquote>

<blockquote><b>4. Username and Password</b><br>
If you do not know what they are, just leave them blank to see if the connection will success. Because in most cases, you do not need them.</blockquote>''', QtWidgets.QMessageBox.Ok)
        reply.exec_()

    # called by button toggled signal.
    def set_next_button_state(self, state):
        if state:
            self.button(QtWidgets.QWizard.NextButton).setEnabled(False)
        else:
            self.button(QtWidgets.QWizard.NextButton).setEnabled(True)

    ''' This function will be called by
    self.comboBox.currentIndexChanged[str].connect(self.option_changed)
    It will pass a parameter text which is the context in the current comboBox
    '''
    def option_changed(self, text):
        if text == 'HTTP / HTTPS':
            self.label_6.setVisible(True)  # username label
            self.lineEdit_3.setVisible(True)  # username input
            
            self.label_8.setVisible(True)  # password label
            self.lineEdit_4.setVisible(True)  # password input

        elif text == 'SOCKS4':
            # Notice that SOCKS4 does not support proxy username and password
            # Therefore, should be the input should be disabled for usability

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
        if state:
            self.label_8.setVisible(True)
            self.lineEdit_4.setVisible(True)
            self.groupBox.setVisible(True)
        else:
            self.label_8.setVisible(False)
            self.lineEdit_4.setVisible(False)
            self.groupBox.setVisible(False)


class TorrcPage(QtWidgets.QWizardPage):
    def __init__(self):
        super(TorrcPage, self).__init__()

        self.steps = Common.wizard_steps

        self.icon = QtWidgets.QLabel(self)

        '''
        self.text = QtWidgets.QTextBrowser(self)
        '''
        self.layout = QtWidgets.QVBoxLayout(self)
        self.label = QtWidgets.QLabel(self)
        self.layout.addWidget(self.label)


        #self.layout = QtWidgets.QGridLayout()

        self.groupBox = QtWidgets.QGroupBox(self)
        self.label_2 = QtWidgets.QLabel(self.groupBox)
        self.label_3 = QtWidgets.QLabel(self.groupBox)
        self.label_4 = QtWidgets.QLabel(self.groupBox)
        self.label_5 = QtWidgets.QLabel(self.groupBox)
        self.label_6 = QtWidgets.QLabel(self.groupBox)
        self.label_7 = QtWidgets.QLabel(self.groupBox)
        self.pushButton = QtWidgets.QPushButton(self.groupBox)
        self.horizontal_line = QFrame(self.groupBox)
        self.torrc = QtWidgets.QTextBrowser(self.groupBox)

        self.layout.addWidget(self.groupBox)

        self.show_detail = False
        self.setupUi()

    def setupUi(self):
        font_title = Common.font_title
        font_description_main = Common.font_description_main
        font_description_minor = Common.font_description_minor
        font_option = Common.font_option

        self.label.setText('   Summary')
        self.label.setFont(font_title)

        self.icon.setAlignment(QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.icon.setMinimumSize(50, 0)

        self.groupBox.setMinimumSize(QtCore.QSize(16777215, 343))
        self.groupBox.setGeometry(0, 20, 0, 0)
        self.groupBox.setFlat(True)

        self.label_2.setGeometry(QtCore.QRect(80, 20, 100, 50))
        self.label_2.setText(" Status: ")
        self.label_2.setFont(font_description_minor)

        self.label_3.setGeometry(QtCore.QRect(140, 20, 500, 50))
        self.label_3.setText("Void")
        self.label_3.setFont(font_option)

        self.label_4.setGeometry(QtCore.QRect(80, 47, 100, 50))
        self.label_4.setText("Bridges: ")
        self.label_4.setFont(font_description_minor)

        self.label_5.setGeometry(QtCore.QRect(140, 47, 500, 50))
        self.label_5.setText("Void")
        self.label_5.setFont(font_option)

        self.label_6.setGeometry(QtCore.QRect(80, 75, 100, 50))
        self.label_6.setText("   Proxy: ")
        self.label_6.setFont(font_description_minor)

        self.label_7.setGeometry(QtCore.QRect(140, 75, 500, 50))
        self.label_7.setText("Void")
        self.label_7.setFont(font_option)

        '''
        self.text.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.text.setAlignment(QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        '''

        #self.layout.addWidget(self.icon, 0, 0, 1, 1)
        #self.layout.addWidget(self.groupBox, 0, 0, 1, 1)

        '''
        self.layout.addWidget(self.text, 0, 1, 1, 2)
        '''
        #self.layout.addWidget(self.torrc, 1, 1, 1, 1)

        self.setLayout(self.layout)

        self.pushButton.setEnabled(True)
        self.pushButton.setGeometry(QtCore.QRect(430, 100, 86, 25))
        self.pushButton.setText('&Details')
        self.pushButton.clicked.connect(self.detail)

        self.horizontal_line.setFrameShape(QFrame.HLine)
        self.horizontal_line.setFrameShadow(QFrame.Sunken)
        self.horizontal_line.setGeometry(15, 130, 510, 5)


        # This is the QTextEdit that shows torrc files
        self.torrc.setVisible(self.show_detail)
        self.torrc.setGeometry(QtCore.QRect(20, 145, 500, 190))
        self.torrc.setStyleSheet("background-color:white;")
        # Allow long input appears in one line.
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

        '''
        reply = QtWidgets.QMessageBox(QtWidgets.QMessageBox.NoIcon, 'torrc settings', open(Common.torrc_file_path).read(), QtWidgets.QMessageBox.Ok)
        reply.exec_()
        '''

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
        font_description_minor = Common.font_description_minor
        font_description_main = Common.font_description_main
        font_option = Common.font_option


        self.text.setFont(font_description_main)
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

        self.parseTorrc()


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

        self.setupUi()


    def setupUi(self):
        self.setWindowIcon(QtGui.QIcon("/usr/share/icons/anon-icon-pack/whonix.ico"))
        self.setWindowTitle('Anon Connection Wizard')
        self.resize(580, 400)

        self.setWindowFlags(self.windowFlags() | QtCore.Qt.CustomizeWindowHint)
        # disable (but not hide) close button
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowCloseButtonHint)

        
        # signal-and-slot
        self.button(QtWidgets.QWizard.BackButton).clicked.connect(self.back_button_clicked)
        self.button(QtWidgets.QWizard.NextButton).clicked.connect(self.next_button_clicked)
        self.button(QtWidgets.QWizard.CancelButton).clicked.connect(self.cancel_button_clicked)

        # Since this is the index page, no back_button is needed.
        self.button(QtWidgets.QWizard.BackButton).setVisible(False)
        self.button(QtWidgets.QWizard.BackButton).setEnabled(False)


        self.CancelButtonOnLeft
        self.button(QtWidgets.QWizard.CancelButton).setVisible(True)
        self.button(QtWidgets.QWizard.CancelButton).setEnabled(True)
        self.button(QtWidgets.QWizard.CancelButton).setText('Quit')
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
        ## TODO: new implementation will not need this
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

        if self.currentId() == self.steps.index('bridge_wizard_page_1'):
            Common.from_bridge_page_1 = True
            

            # Common.from_bridge_page_1 serves as a falg to work around the bug that
            # message jump out when switching from proxy_wizard_page_1 to proxy_wizard_page_2
            if not Common.from_bridge_page_1:
                # TODO: we may use re to check if the bridge input is valid
                if (not Common.use_default_bridge) and Common.bridge_custom == "":
                    self.reply = QtWidgets.QMessageBox(QtWidgets.QMessageBox.NoIcon, 'Warning',
                        '''<p><b>  Custom bridge list is blank</b></p>
                        <p> Please input valid custom bridges or use provided bridges instead.</p>''', QtWidgets.QMessageBox.Ok)
                    self.reply.exec_()
            Common.from_bridge_page_1 = False

        if self.currentId() == self.steps.index('proxy_wizard_page_1'):
            Common.to_proxy_page_2 = True
            
        if self.currentId() == self.steps.index('proxy_wizard_page_2'):
            # TODO: use re to detect if the formatt of IP and port is not correct
            # The dificulty is that the IP can be hostname which is almost free form
            # Common.to_proxy_page_2 serves as a falg to work around the bug that
            # message jump out when switching from proxy_wizard_page_1 to proxy_wizard_page_2
            if not Common.to_proxy_page_2:
                if Common.proxy_ip == "" or Common.proxy_port == "":
                    self.reply = QtWidgets.QMessageBox(QtWidgets.QMessageBox.NoIcon, 'Warning',
                        '''<p><b>  IP and/or Port is blank</b></p>
                        <p> Please input a proper IP and Port number.</p>''', QtWidgets.QMessageBox.Ok)
                    self.reply.exec_()
            Common.to_proxy_page_2 = False
            
        if self.currentId() == self.steps.index('torrc_page'):
            self.resize(580, 400)
            self.button(QtWidgets.QWizard.BackButton).setVisible(True)
            self.button(QtWidgets.QWizard.CancelButton).setVisible(True)
            self.button(QtWidgets.QWizard.FinishButton).setVisible(False)
            #self.center()

            ''' io() will wirte lines to /etc/torrc.d/anon_connection_wizard.torrc
            basing on user's selection in anon_connection_wizard
            '''
            self.io()
            
            ''' displace the torrc file and icon used on the page
            notice that anon_connection_wizard.torrc will not have line about DisableNetwork 0
            That line will be changed by tor_status module in /etc/torrc
            '''


            if not Common.disable_tor:
                #self.torrc_page.text.setText(self._('tor_enabled'))  # Q: how does this line work?

                self.torrc_page.label_3.setText('Tor will be enabled.')
                if not Common.use_bridges:
                    self.torrc_page.label_5.setText('None Selected')
                else:
                    if Common.use_default_bridge:
                        if Common.bridge_type == 'obfs3':
                            self.torrc_page.label_5.setText('Provided obfs3')
                        elif Common.bridge_type == 'scramblesuit':
                            self.torrc_page.label_5.setText('Provided scramblesuit')
                        elif Common.bridge_type == 'obfs4':
                            self.torrc_page.label_5.setText('Provided obfs4')
                    else:
                        if Common.bridge_custom.startswith('obfs3'):
                            self.torrc_page.label_5.setText('Custom obfs3')
                        elif Common.bridge_custom.startswith('obfs4'):
                            self.torrc_page.label_5.setText('Custom obfs4')

                self.torrc_page.label_7.setText('Tor will be enabled.')
                torrc_text = open(Common.torrc_tmp_file_path).read()
                self.torrc_page.torrc.setPlainText(torrc_text)
                self.torrc_page.icon.setPixmap(QtGui.QPixmap( \
                    '/usr/share/icons/oxygen/48x48/status/task-complete.png'))
            else:
                #self.torrc_page.text.setText(self._('tor_disabled'))
                self.torrc_page.label_3.setText('Tor will be disabled.')
                self.torrc_page.label_4.setVisible(False)
                self.torrc_page.label_5.setVisible(False)
                self.torrc_page.label_6.setVisible(False)
                self.torrc_page.label_7.setVisible(False)
                self.torrc_page.pushButton.setVisible(False)
                torrc_text = open(Common.torrc_file_path).read()
                self.torrc_page.torrc.setPlainText(torrc_text)
                self.torrc_page.icon.setPixmap(QtGui.QPixmap( \
                    '/usr/share/icons/oxygen/48x48/status/task-attention.png'))

            if not Common.use_proxy:
                self.torrc_page.label_7.setText('None Selected')
            else:
                if Common.proxy_type == 'HTTP/HTTPS':
                    self.torrc_page.label_7.setText('HTTP(S)  {0} : {1}'.format(Common.proxy_ip, Common.proxy_port))
                elif Common.proxy_type == 'SOCKS4':
                    self.torrc_page.label_7.setText('Socks4  {0} : {1}'.format(Common.proxy_ip, Common.proxy_port))
                elif Common.proxy_type == 'SOCKS5':
                    self.torrc_page.label_7.setText('Socks5  {0} : {1}'.format(Common.proxy_ip, Common.proxy_port))

            # move the tmp file to the real .torrc
            # this may overwrite the previous .torrc, but it does not matter
            shutil.move(Common.torrc_tmp_file_path, Common.torrc_file_path)


        if self.currentId() == self.steps.index('tor_status_page'):
            self.tor_status_page.text.setText('')  # This will clear the text left by different Tor status statement
            if self.tor_status == 'tor_enabled' or self.tor_status == 'tor_already_enabled':
                self.tor_status_page.bootstrap_progress.setVisible(True)

            self.button(QtWidgets.QWizard.BackButton).setVisible(True)
            self.button(QtWidgets.QWizard.CancelButton).setVisible(True)
            self.button(QtWidgets.QWizard.FinishButton).setVisible(False)

            '''Arranging different tor_status_page according to the value of disable_tor.'''
            if not Common.disable_tor:
                # tor_status.set_disabled() does two things:
                # 1. change the line '#DisableNetwork 0' to 'DisableNetwork 0' in /etc/tor/torrc
                # 2. restart Tor
                self.tor_status = tor_status.set_enabled()
                
                self.tor_status_page.text.setText('')  # This will clear the text left by different Tor status statement
                
                if self.tor_status == 'tor_enabled' or self.tor_status == 'tor_already_enabled':
                    self.tor_status_page.bootstrap_progress.setVisible(True)
                    '''This line below will create a Tor Bootstrap instance,
                    which will try to connect to Tor's socket '/run/tor/control'.
                    Since the socket will only exist when Tor is started,
                    we should be careful that this line should always be placed behind tor_status.setEnabled().
                    Additionally, since the generation of /run/tor/control takes a little bit time,
                    we may have to wait until the file is generated. 
                    Otherwise, a '/run/tor/control not found' bug will raise.

                    Although it makes sense to implement the "wait for /run/tor/control generated"
                    here, we do the implementation in connect_to_control_port() in TorBootstrap Class.
                    This is because of usability concern, we don't want users feel nothing happened,
                    after they clicked the NextButton.
                    '''
                    
                    self.bootstrap_thread = TorBootstrap(self)
                    self.bootstrap_thread.signal.connect(self.update_bootstrap)
                    self.bootstrap_thread.finished.connect(self.show_finish_button)
                    self.bootstrap_thread.start()
                else:
                    print('Unexpected tor_status: ' + self.tor_status)
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
            self.bootstrap_done = False
            self.button(QtWidgets.QWizard.FinishButton).setVisible(False)
            self.button(QtWidgets.QWizard.CancelButton).setVisible(True)

        if self.currentId() == self.steps.index('proxy_wizard_page_1'):
            Common.to_proxy_page_2 = True
            self.bootstrap_done = False
            self.button(QtWidgets.QWizard.FinishButton).setVisible(False)
            self.button(QtWidgets.QWizard.CancelButton).setVisible(True)

    def show_finish_button(self):
        if self.bootstrap_done or Common.disable_tor:
            self.button(QtWidgets.QWizard.CancelButton).setVisible(False)
            self.button(QtWidgets.QWizard.FinishButton).setVisible(True)
            self.button(QtWidgets.QWizard.FinishButton).setFocus()


    def io(self):
        repair_torrc.repair_torrc()  # This gurantees a good torrc and the existence of /etc/torrc.d

        # Creates a file and returns a tuple containing both the handle and the path.
        # we are sponsible for removing tmp file when finished which is the reason we use shutil.move(), not shutil.copy(), below
        handle, Common.torrc_tmp_file_path = tempfile.mkstemp()
        with open(handle, "w") as f:
            f.write("# This file is generated by anon-connection-wizard.\n\
# Anything specified here will override Whonix's default Tor config customizations in /usr/share/tor/tor-service-defaults-torrc\n\
# Changes to this file should ONLY be made through anon-connection-wizard or error may occur.\n\
# However, deleting this file will not cause severe problem since a new file will be generated by running anon-connection-wizard again.\n\
# All user's configuration should go to /etc/tor/torrc, not here. Because this file can be easily overwritten by anon-connection-wizard.\n\n")
        
        

        ''' This part is the IO to torrc for bridges settings.
        Related official docs: https://www.torproject.org/docs/tor-manual.html.en
        '''
        if Common.use_bridges:
            with open(Common.torrc_tmp_file_path, 'a') as f:
                f.write(Common.command_useBridges + '\n')
                if Common.use_default_bridge:
                    if Common.bridge_type == 'obfs3':
                        f.write(Common.command_obfs3 + '\n')
                    elif Common.bridge_type == 'scramblesuit':
                        f.write(Common.command_scramblesuit + '\n')
                    elif Common.bridge_type == 'obfs4':
                        f.write(Common.command_obfs4 + '\n')
                        # More types of bridges will be availble once Whonix support them: meek, flashproxy
                    elif Common.bridge_type == '':
                        pass
                    bridges = json.loads(open(Common.bridges_default_path).read())  # default bridges will be loaded, however, what does the variable  bridges do? A: for bridge in bridges
                    # Q: What does json.load do?
                    for bridge in bridges['bridges'][Common.bridge_type]:  # What does this line mean? A: The bridges are more like a multilayer-dictionary
                        f.write('Bridge {0}\n'.format(bridge))  # This is the format to configure a bridge in torrc
                else:  # Use custom bridges
                    f.write(Common.command_use_custom_bridge + '\n')  # mark custom bridges are used
                    
                    if Common.bridge_custom.startswith('obfs4'):
                        f.write(Common.command_obfs4 + '\n')
                    elif Common.bridge_custom.startswith('obfs3'):
                        f.write(Common.command_obfs3 + '\n')
                    elif Common.bridge_custom.startswith('fte'):
                        f.write(Common.command_fte + '\n')
                    elif Common.bridge_custom.startswith('meek-amazon'):
                        pass  # Wait to be implemented in Whonix.
                    elif Common.bridge_custom.startswith('meek-azure'):
                        pass

                    # Write the specific bridge address, port, cert etc.
                    bridge_custom_list = Common.bridge_custom.split('\n')
                    for bridge in bridge_custom_list:
                        if bridge != '':  # check if the line is actually empty
                            f.write('Bridge {0}\n'.format(bridge))


        ''' The part is the IO to torrc for proxy settings.
        Related official docs: https://www.torproject.org/docs/tor-manual.html.en
        '''
        if Common.use_proxy:
            with open(Common.torrc_tmp_file_path, 'a') as f:
                if Common.proxy_type == 'HTTP/HTTPS':
                    f.write('HTTPSProxy {0}:{1}\n'.format(Common.proxy_ip, Common.proxy_port))
                    if (Common.proxy_username != ''):  # there is no need to check password because username is essential
                        f.write('HTTPSProxyAuthenticator {0}:{1}\n'.format(Common.proxy_username, Common.proxy_password))
                elif Common.proxy_type == 'SOCKS4':
                    # Notice that SOCKS4 does not support proxy username and password
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

    def parseTorrc(self):
        if os.path.exists(Common.torrc_file_path):
            with open(Common.torrc_file_path, 'r') as f:
                for line in f:
                    if line.startswith(Common.command_use_custom_bridge):  # this condition must be above '#' condition, because it also contains '#'
                        Common.use_default_bridge = False
                    elif line.startswith('#'):
                        pass  # add this line to improve efficiency
                    elif line.startswith(Common.command_useBridges):
                        Common.use_bridges = True
                    elif line.startswith(Common.command_obfs3):
                        Common.bridge_type = 'obfs3'
                    elif line.startswith(Common.command_obfs4):
                        Common.bridge_type = 'obfs4 (recommended)'
                    elif line.startswith(Common.command_fte):
                        Common.bridge_type = 'fte'
                    elif line.startswith(Common.command_scramblesuit):
                        Common.bridge_type = 'scramblesuit'
                    elif line.startswith(Common.command_bridgeInfo):
                        Common.bridge_custom += ' '.join(line.split(' ')[1:])  # eliminate the 'Bridge'
                    elif line.startswith(Common.command_http):
                        Common.use_proxy = True
                        Common.proxy_type = 'HTTP / HTTPS'
                        Common.proxy_ip = line.split(' ')[1].split(':')[0] # this is too fixed, which is not good implementation. But as long as leave .torrc untouched by user, it will be Okay. We should also be caureful when changing the command line format in this app
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

class TorBootstrap(QtCore.QThread):
    signal = QtCore.pyqtSignal(str)
    def __init__(self, main):
        #super(TorBootstrap, self).__init__(main)
        QtCore.QThread.__init__(self, parent=None)

        #self.signal = QtCore.SIGNAL("signal")  # Not usable in PyQt5 anymore
        self.previous_status = ''
        self.bootstrap_percent = 0
        #self.is_running = False
        self.tor_controller = self.connect_to_control_port()

    def connect_to_control_port(self):
        import stem
        import stem.control
        import stem.socket
        from stem.connection import connect        

        '''
        In case something wrong happened when trying to start Tor,
        causing /run/tor/control never be generated.
        We set up a time counter and hardcode the wait time limitation as 15s.
        '''
        self.count_time = 0
        while(not os.path.exists(Common.control_socket_path) and self.count_time < 15):
            self.previous_status = 'Waiting for /run/tor/control...'
            time.sleep(0.2)
            self.count_time += 0.2

        if os.path.exists(Common.control_socket_path):
            self.tor_controller = stem.control.Controller.from_socket_file(Common.control_socket_path)
        else:
            print(Common.control_socket_path + ' not found!!!')

        if not os.path.exists(Common.control_cookie_path):
            # TODO: can we let Tor generate a cookie to fix this situiation?
            print(Common.control_cookie_path + ' not found!!!')
        else:
            with open(Common.control_cookie_path, "rb") as f:
                cookie = f.read()
            try:
                self.tor_controller.authenticate(cookie)
            except stem.connection.IncorrectCookieSize:
                pass  #if the cookie file's size is wrong
            except stem.connection.UnreadableCookieFile:
                pass  #if # TODO: he cookie file doesn't exist or we're unable to read it
            except stem.connection.CookieAuthRejected:
                pass  #if cookie authentication is attempted but the socket doesn't accept it
            except stem.connection.IncorrectCookieValue:
                pass  #if the cookie file's value is rejected
        return self.tor_controller

    
    def run(self):
        #self.is_running = True
        while self.bootstrap_percent < 100:
            bootstrap_status = self.tor_controller.get_info("status/bootstrap-phase")
            self.bootstrap_percent = int(re.match('.* PROGRESS=([0-9]+).*', bootstrap_status).group(1))
            if bootstrap_status != self.previous_status:
                sys.stdout.write('{0}\n'.format(bootstrap_status))
                sys.stdout.flush()
                self.previous_status = bootstrap_status
                self.signal.emit(bootstrap_status)
            time.sleep(0.2)


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
