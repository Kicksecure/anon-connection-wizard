#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-

'''
This product is produced independently from the Tor® anonymity software and carries no guarantee from The Tor Project about quality, suitability or anything else.

You can verify the original source of Tor for yourselves by visiting the official Tor website: https://www.torproject.org/
'''

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

    init_tor_status = ''  # it records the initial status of Tor, serving as a backup
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
<<<<<<< HEAD
    command_meek_lite = 'ClientTransportPlugin meek_lite exec /usr/bin/obfs4proxy'
    command_meek_amazon_address = 'a0.awsstatic.com\n'
    command_meek_azure_address = 'ajax.aspnetcdn.com\n'
    
    command_meek_lite = 'ClientTransportPlugin meek_lite exec /usr/bin/obfs4proxy'
=======
>>>>>>> upstream/master
    command_bridgeInfo = 'bridge '
    
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
    from_proxy_page_1 = True
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


    '''The following parameters indicates the size and locatino of the groupBox used each page.
    '''
    groupBox_width = 350
    groupBox_height = 345

    #groupBox_location_
    
    if not os.path.exists('/var/cache/whonix-setup-wizard/status-files'):
        os.makedirs('/var/cache/whonix-setup-wizard/status-files')

    if not os.path.exists('/var/cache/whonix-setup-wizard/status-files/whonix_connection.done'):
        ## "not whonix_connection.done" is required once at first run to get a copy of the original torrc.
        f = open('/var/cache/whonix-setup-wizard/status-files/whonix_connection.done', 'w')
        f.close()
        
    wizard_steps = ['connection_main_page',
                    'bridge_wizard_page_2',
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

v    def show_disable_tor(self):
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
            return self.steps.index('bridge_wizard_page_2')
        elif self.pushButton_3.isChecked():
            Common.disable_tor = True
            return self.steps.index('tor_status_page')

class BridgesWizardPage2(QtWidgets.QWizardPage):
    def __init__(self):
        super(BridgesWizardPage2, self).__init__()

        self.steps = Common.wizard_steps

        self.bridges = ['obfs4 (recommended)',
<<<<<<< HEAD
                        'obfs3',
                        'meek-amazon (works in China)',
                        'meek-azure'
                        # The following will be uncommented as soon as being implemented.
                        # Detail: https://github.com/Whonix/anon-connection-wizard/pull/2
                        # 'fte'
=======
                        'obfs3'
                        # The following will be uncommented as soon as being implemented.
                        # Detail: https://github.com/Whonix/anon-connection-wizard/pull/2
                        # 'fte',
                        # 'meek-amazon',
                        # 'meek-azure'
>>>>>>> upstream/master
                       ]

        self.layout = QtWidgets.QVBoxLayout(self)

        self.label = QtWidgets.QLabel(self)
        self.layout.addWidget(self.label)

        '''
        self.label_2 = QtWidgets.QLabel(self)
        self.layout.addWidget(self.label_2)
        '''
        
        self.groupBox = QtWidgets.QGroupBox(self)
        self.layout.addWidget(self.groupBox)

        self.checkBox = QtWidgets.QCheckBox(self.groupBox)  # bridge checkBox
        self.pushButton_show_help_censorship = QtWidgets.QPushButton(self.groupBox)
        
        '''
        self.groupBox_default = QtWidgets.QGroupBox(self)
        self.groupBox_custom = QtWidgets.QGroupBox(self)
        '''
        self.horizontal_line_1 = QFrame(self.groupBox)
        
        self.default_button = QtWidgets.QRadioButton(self.groupBox)

        self.horizontal_line_2 = QFrame(self.groupBox)
                
        self.custom_button = QtWidgets.QRadioButton(self.groupBox)

        self.label_3 = QtWidgets.QLabel(self.groupBox)
        self.comboBox = QtWidgets.QComboBox(self.groupBox)
        
        self.label_4 = QtWidgets.QLabel(self.groupBox)
        self.custom_bridges = QtWidgets.QTextEdit(self.groupBox)  # QTextEdit box for bridges.
        self.pushButton_show_help_bridge = QtWidgets.QPushButton(self.groupBox)

        self.label_5 = QtWidgets.QLabel(self.groupBox)
        
        self.setupUi()

    def setupUi(self):
        self.label.setMinimumSize(QtCore.QSize(16777215, 35))

        font_title = Common.font_title
        font_description_main = Common.font_description_main
        font_description_minor = Common.font_description_minor
        font_option = Common.font_option

        self.label.setText('   Tor Bridges Configuration')
        self.label.setFont(font_title)
        self.label.setGeometry(QtCore.QRect(0, 0, 0, 0))


        self.checkBox.setChecked(Common.use_bridges)
        self.checkBox.stateChanged.connect(self.enable_bridge)
        self.checkBox.setText("I need Tor bridges to bypass the Tor censorship.")
        self.checkBox.setFont(font_description_main)
        self.checkBox.setToolTip("")  # ToolTip may not be needed since a help button is offered
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
        self.default_button.setText('Connect with provided bridges')
        self.default_button.setFont(font_description_minor)

        self.horizontal_line_2.setFrameShape(QFrame.HLine)
        self.horizontal_line_2.setFrameShadow(QFrame.Sunken)
        self.horizontal_line_2.setGeometry(15, 140, 510, 5)


        self.custom_button.setGeometry(QtCore.QRect(18, 160, 500, 25))
        self.custom_button.setText('Enter custom bridges')
        self.custom_button.setFont(font_description_minor)

        if Common.use_default_bridge:
            self.default_button.setChecked(True)
        else:
            self.custom_button.setChecked(True)

        # This will emit a signal every time default_button is toggled
        self.default_button.toggled.connect(self.show_default_bridge)

        self.label_3.setGeometry(QtCore.QRect(40, 110, 106, 20))
        self.label_3.setText('Transport type:')
        self.label_3.setFont(font_description_minor)

        # This is the how to make a comboBox. The variable bridges is defined above.
        # The proxy type selection in ProxyWizardPage2 can also use this method.
<<<<<<< HEAD
        self.comboBox.setGeometry(QtCore.QRect(150, 107, 230, 27))
=======
        self.comboBox.setGeometry(QtCore.QRect(140, 110, 181, 27))
>>>>>>> upstream/master
        for bridge in self.bridges:
            self.comboBox.addItem(bridge)
            
        # The default value is adjust according to Common.bridge_type
        if Common.use_default_bridge:
            self.comboBox.setCurrentIndex(self.bridges.index(Common.bridge_type))

        self.label_4.setEnabled(False)
        self.label_4.setGeometry(QtCore.QRect(38, 185, 300, 20))
        self.label_4.setText('Enter one or more bridge relay (one per line).')

        # TODO: The boolean value of this should be the same with self.custom_button.isChecked() Q: How to do it dynamically? A: signal-and-slot.
        # Notice that this feature is not in Tor launcher, this can be an improvement which also benefits upstream.
        # TODO: Make this QTextEdit support syntax to make it even more clear to users what should be input: https://doc.qt.io/archives/qq/qq21-syntaxhighlighter.html
        self.custom_bridges.setEnabled(True)
        self.custom_bridges.setGeometry(QtCore.QRect(38, 205, 500, 76))
        self.custom_bridges.setStyleSheet("background-color:white;")
        # Allow long input appears in one line.
        self.custom_bridges.setLineWrapColumnOrWidth(1800)
        self.custom_bridges.setLineWrapMode(QtWidgets.QTextEdit.FixedPixelWidth)
        
        if not Common.use_default_bridge:
            self.custom_bridges.setText(Common.bridge_custom)  # adjust the line according to value in Common

        # TODO: The next statement can not be used yet,
        # this is because the QTextEdit does not supprot setPlaceholderText.
        # More functions need to be added to implement that:
        # https://doc.qt.io/archives/qq/qq21-syntaxhighlighter.html
        # self.custom_bridges.setPlaceholderText('type address:port')

        self.pushButton_show_help_bridge.setEnabled(True)
        self.pushButton_show_help_bridge.setGeometry(QtCore.QRect(360, 160, 150, 25))
        self.pushButton_show_help_bridge.setText('&How to get Bridges?')
        self.pushButton_show_help_bridge.clicked.connect(self.show_help_bridge)

        self.label_5.setVisible(True)
        self.label_5.setGeometry(10, 300, 500, 15)
        self.label_5.setText(Common.assistance)
        self.label_5.setFont(font_description_minor)

        ## Set the visibility of each item.
        ## Notice that some item has two boolean to decide the visibility
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
                if bridge_type.startswith('obfs3'):
                    bridge_type = 'obfs3'
                elif bridge_type.startswith('obfs4'):
                    bridge_type = 'obfs4'
<<<<<<< HEAD
                elif bridge_type.startswith('meek-amazon'):
                    bridge_type = 'meek-amazon'
                elif bridge_type.startswith('meek-azure'):
                    bridge_type = 'meek-azure'

=======
>>>>>>> upstream/master
                # elif bridge_type.selftartswith('scramblesuit'):
                #    bridge_type = 'scramblesuit'
                ''' TODO: Other options can be implemented once whonix supports them
                Detail: https://github.com/Whonix/anon-connection-wizard/pull/2
                elif bridge_type.startswith('fte'):
                bridge_type = 'fte'
<<<<<<< HEAD
=======
                elif bridge_type.startswith('meek-amazon'):
                bridge_type = 'meek-amazon'
                elif bridge_type.startswith('meek-azure'):
                bridge_type = 'meek-azure'
>>>>>>> upstream/master
                '''
                Common.bridge_type = bridge_type
                Common.use_default_bridge = True

                return self.steps.index('proxy_wizard_page_2')

            elif self.custom_button.isChecked():
                Common.bridge_custom = str(self.custom_bridges.toPlainText())
                Common.use_default_bridge = False

                # TODO: a more gerneral RE will help filter the case where bridge_custom input is invaild
                if not self.valid_bridge(Common.bridge_custom):
                    return self.steps.index('bridge_wizard_page_2') # stay at the page until a bridge is given'''
                else:
                    return self.steps.index('proxy_wizard_page_2')

    def valid_bridge(self, bridges):
        # TODO: we may use re to check if the bridge input is valid
        # we should examine if every line follows the pattern
        # obfs3 ip:port
        # obfs4 ip:port
        # ip:port (vanilla bridge)
<<<<<<< HEAD
        # If this problem is not solved, anon-connection-wizard will not support vanilla bridge!!
        # IPv6 bridges are not even availble in bridgeDB,
        # so we do not need to care it too much currently
        
        #if bridges == "" or bridges.isspace():
        #    return False

        bridge_defined_type = bridges.split(' ')[0]
        bridge_defined_type = bridge_defined_type.lower()

        if (bridge_defined_type.startswith('obfs3')
                or bridge_defined_type.startswith('obfs4')
                or bridge_defined_type.startswith('meek_lite')
            ## This case try to match vanilla bridges.
            ## Example, trying to match "109.23.3.9:8236"
            ## This is dirty but hopefully it is effective
                or (('.' in bridge_defined_type) and (':' in bridge_defined_type))):
            return True
        else:
            return False

=======
        if bridges == "" or bridges.isspace():
            return False

        '''
        # In order to make a vanilla bridge usable, we need to comment these
        bridges_list = bridges.splitlines()
        for bridge in bridges_list:
            if (not bridge.isspace()) and (not bridges == ""):
                bridge = bridge.lower()
                if bridge.startswith('obfs3') or bridge.startswith('obfs4'):
                    pass
                else:
                    return False
        '''
        return True
                    


>>>>>>> upstream/master
    def show_help_censorship(self):
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



    def show_help_bridge(self):
        reply = QtWidgets.QMessageBox(QtWidgets.QMessageBox.NoIcon, 'Bridges Configuration Help',
                                  '''<p><b>  Bridge Relay Help</b></p>

<p>If you are unable to connect to the Tor network, it could be that your Internet Service
Provider (ISP) or another agency is blocking Tor.  Often, you can work around this problem
by using Tor Bridges, which are unlisted relays that are more difficult to block.</p>

<p>You may use the preconfigured, provided set of bridge addresses or you may obtain a
                                  custom set of addresses by using one of these two methods:</p>

<blockquote><b>1. Through the Web</b><br>
Use a web browser to visit:<br>
https://bridges.torproject.org/options</blockquote>

<blockquote><b>2. Through the Email Autoresponder</b><br>
Send email to bridges@torproject.org with the line 'get bridges' by itself in the body
of the message.  However, to make it harder for an attacker to learn a lot of bridge
addresses, you must send this request from one of the following email providers
(listed in order of preference):<br>
https://www.riseup.net, https://mail.google.com, or https://mail.yahoo.com</blockquote>

<p> Notice that when choosing the bridge type, only <b>obfs3</b> and <b>obfs4</b> are supported currently.<br><br>
The bridges you paste into the custom bridge box should look like these:</p>

<blockquote><b>1. For obfs3 bridges</b><br>
obfs3 204.94.56.79:80 A09D536DD1752D542E1FBB3C9CE4449D51298239<br>
obfs3 109.105.109.190:6789 1E05F577A0EC0213F971D81BF4D86A9E4E8229ED</blockquote>

<blockquote><b>2. For obfs4 bridges</b><br>
obfs4 154.35.22.89:80 8FB9F4319E89E5C6223052AA525A192AFBC85D55 cert=GGGS1TX4R81m3r0HBl79wKy1OtPPNR2CZUIrHjkRg65Vc2VR8fOyo64f9kmT1UAFG7j0HQ iat-mode=0<br>
obfs4 109.15.109.12:10527 8DFCD8FB3285E855F5A55EDDA35696C743ABFC4E cert=Bvg/itxeL4TWKLP6N1MaQzSOC6tcRIBv6q57DYAZc3b2AzuM+/TfB7mqTFEfXILCjEwzVA iat-mode=1</blockquote>
'''
                                      , QtWidgets.QMessageBox.Ok)
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
        ## state is a boolean indicating if checkBox is checked or not
        ## Notice that some item has two boolean to decide the visibility
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


        self.groupBox = QtWidgets.QGroupBox(self)
        self.layout.addWidget(self.groupBox)
        
        self.checkBox = QtWidgets.QCheckBox(self.groupBox)  # proxy checkBox

        self.horizontal_line = QFrame(self.groupBox)
        
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

        self.setupUi()

    def setupUi(self):
        self.label.setMinimumSize(QtCore.QSize(16777215, 35))

        font_title = Common.font_title
        font_description_main = Common.font_description_main
        font_description_minor = Common.font_description_minor
        font_option = Common.font_option


        self.label.setText('   Local Proxy Configuration')
        self.label.setFont(font_title)

        self.groupBox.setMinimumSize(QtCore.QSize(Common.groupBox_width, Common.groupBox_height))
        self.groupBox.setGeometry(QtCore.QRect(0, 20, 0, 0))
        self.groupBox.setFlat(True)

        
        self.checkBox.setChecked(Common.use_proxy)
        self.checkBox.stateChanged.connect(self.enable_proxy)
        self.checkBox.setText("Use proxy before connecting to the Tor network")
        self.checkBox.setFont(font_description_main)
        self.checkBox.setToolTip('''<p>In some situiations, you may want to transfer your traffic through a proxy server before connecting to the Tor network. </p><p>For example, if you are trying to use a third-party censorship circumvention tool to bypass the Tor censorship, you need to configure Tor to connect to the listening port of that circumvention tools. </p>''')
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

        # Here we are going to implement the proxy type selection
        # Change it to larger so  that all options fit
        self.comboBox.setGeometry(QtCore.QRect(118, 110, 121, 27))
        for proxy in self.proxies:
            self.comboBox.addItem(proxy)

        # The default value is adjust according to Common.proxy_type
        if Common.use_proxy:
            self.comboBox.setCurrentIndex(self.proxies.index(Common.proxy_type))

        self.label_5.setGeometry(QtCore.QRect(10, 150, 106, 20))
        self.label_5.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_5.setText("Address: ")
        self.label_5.setFont(font_description_minor)

        '''Username and Password options should be hide
        using "advance" button because it is not used rarely,
        according to recommendation from previous research.
        '''
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


        ''' More instruction should be given as default.
        1. tooltip for each option
        2. option for users to configure well-known third party automatically (We can take foxyproxy's default setting as references.)
        '''
        self.lineEdit.setGeometry(QtCore.QRect(118, 150, 260, 25))
        self.lineEdit.setStyleSheet("background-color:white;")
        self.lineEdit.setPlaceholderText('Example: 127.0.0.1')
        self.lineEdit.setText(Common.proxy_ip)  # TODO: investigate why it does not work
        # TODO: may exchange the sequence of setText and setPlaceholderText
        
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

        # Show proxy settings according to previous settings
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
        self.lineEdit_4.setVisible(Common.use_proxy)
        self.pushButton.setVisible(Common.use_proxy)


    def nextId(self):
        if not self.checkBox.isChecked():
            Common.use_proxy = False
            return self.steps.index('torrc_page')
        else:
            Common.use_proxy = True

            if self.valid_ip(self.lineEdit.text()) and self.valid_port(self.lineEdit_2.text()):
                # if self.default_button.isChecked():
                proxy_type = str(self.comboBox.currentText())

                '''
                # The following was useful when '-' proxy type option was availble,
                # which is not true now.
                if proxy_type.startswith('-'):
                use_proxy = False
                proxy_type = '-'
                # stay at the page until a proxy type is selected
                return self.steps.index('proxy_wizard_page_2') 
                '''

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
                return self.steps.index('proxy_wizard_page_2') # stay at the page until a proxy type is selected'''

    def valid_ip(self, ip):
        # TODO: use re to detect if the formatt of IP is not correct
        # The dificulty is that the IP can be hostname which is almost free form
        # However, we should at least check if it is empty
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
        ## state is a boolean indicating if checkBox is checked or not
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
        self.label_3.setText("Probably an error ocurred")
        self.label_3.setFont(font_option)

        self.label_4.setGeometry(QtCore.QRect(80, 47, 100, 50))
        self.label_4.setText("Bridges: ")
        self.label_4.setFont(font_description_minor)

        self.label_5.setGeometry(QtCore.QRect(140, 47, 500, 50))
<<<<<<< HEAD
        self.label_5.setText("Custom vanilla")
=======
        self.label_5.setText("ERROR: Unsupported Type!")
>>>>>>> upstream/master
        self.label_5.setFont(font_option)

        self.label_6.setGeometry(QtCore.QRect(80, 75, 100, 50))
        self.label_6.setText("   Proxy: ")
        self.label_6.setFont(font_description_minor)

        self.label_7.setGeometry(QtCore.QRect(140, 75, 500, 50))
        self.label_7.setText("Probably an error ocurred")
        self.label_7.setFont(font_option)

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


class TorStatusPage(QtWidgets.QWizardPage):
    def __init__(self):
        super(TorStatusPage, self).__init__()

        self.steps = Common.wizard_steps

        self.bootstrap_text = QtWidgets.QLabel(self)
        self.text = QtWidgets.QLabel(self)

        # Creating a progress bar
        self.bootstrap_progress = QtWidgets.QProgressBar(self)

        # Creating a Layout to add all the widgets
        self.layout = QtWidgets.QGridLayout()
        self.setupUi()

    def setupUi(self):
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
        Common.init_tor_status = tor_status.tor_status()

        self.steps = Common.wizard_steps
        # The sequence of adding a page will also be the sequence the pages are shown in a wizard.
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

        # self.bootstrap_thread = TorBootstrap(self)
        # self.bootstrap_thread.finished.connect(app.exit)
        # self.connect(self.bootstrap_thread, self.bootstrap_thread.signal, self.update_bootstrap)
        self.bridges = []
        self.proxy_type = ''
        self.tor_status = ''
        self.bootstrap_done = False

        self.setupUi()


    def setupUi(self):
        self.setWindowIcon(QtGui.QIcon("/usr/share/icons/anon-icon-pack/advancedsettings.ico"))  # whonix-sepecific
        self.setWindowTitle('Anon Connection Wizard')
        self.setFixedSize(580, 450)  # This is important to control the fixed size of the window

        '''
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.CustomizeWindowHint)

        # disable (but not hide) close button
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowCloseButtonHint)
        '''
        
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
        try:
            if self.bootstrap_thread:
                self.bootstrap_thread.terminate()

            ''' recover Tor to the intial status before the starting of anon_connection_wizard
            '''
            if Common.init_tor_status == 'tor_enabled':
                pass
            elif Common.init_tor_status == 'tor_disabled':
                tor_status.set_disabled()

        except AttributeError:
            pass

    def next_button_clicked(self):
        if self.currentId() == self.steps.index('connection_main_page'):
            self.button(QtWidgets.QWizard.CancelButton).setVisible(True)
            self.button(QtWidgets.QWizard.FinishButton).setVisible(False)
            #self.center()
            Common.from_bridge_page_1 = True
            Common.from_proxy_page_1 = True
            
        if self.currentId() == self.steps.index('bridge_wizard_page_2'):
            # Common.from_bridge_page_1 serves as a falg to work around the bug that
            # message jump out when switching from bridge_wizard_page_1 to bridge_wizard_page_2
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
            # Common.from_proxy_page_1 serves as a falg to work around the bug that
            # message jump out when switching from proxy_wizard_page_1 to proxy_wizard_page_2
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
<<<<<<< HEAD
                        elif Common.bridge_type == 'meek-amazon':
                            self.torrc_page.label_5.setText('Provided meek-amazon')
                        elif Common.bridge_type == 'meek-azure':
                            self.torrc_page.label_5.setText('Provided meek-azure')
=======
>>>>>>> upstream/master
                    else:
                        if Common.bridge_custom.lower().startswith('obfs3'):
                            self.torrc_page.label_5.setText('Custom obfs3')
                        elif Common.bridge_custom.lower().startswith('obfs4'):
                            self.torrc_page.label_5.setText('Custom obfs4')
<<<<<<< HEAD
                        elif Common.bridge_custom.lower().startswith('meek_lite'):
                            self.torrc_page.label_5.setText('Custom meek_lite')
                        else:
                            self.torrc_page.label_5.setText('Custom vanilla')
=======
                        else:
                            self.torrc_page.label_5.setText('ERROR: Unsupported Type!')
>>>>>>> upstream/master

                self.torrc_page.label_7.setText('Tor will be enabled.')
                torrc_text = open(Common.torrc_tmp_file_path).read()
                self.torrc_page.torrc.setPlainText(torrc_text)
                #self.torrc_page.icon.setPixmap(QtGui.QPixmap( \
                    #'/usr/share/icons/oxygen/48x48/status/task-complete.png'))
            else:
                ''' Notice that this condition will not be used now, because
                anon_connection_wizard will skip torrc_page when disable_tor is selected to be true.
                However, we still leave the code here in case of any related changes in the future.
                '''
                #self.torrc_page.text.setText(self._('tor_disabled'))
                self.torrc_page.label_3.setText('Tor will be disabled.')
                self.torrc_page.label_4.setVisible(False)
                self.torrc_page.label_5.setVisible(False)
                self.torrc_page.label_6.setVisible(False)
                self.torrc_page.label_7.setVisible(False)
                self.torrc_page.pushButton.setVisible(False)
                torrc_text = open(Common.torrc_file_path).read()
                self.torrc_page.torrc.setPlainText(torrc_text)
                #self.torrc_page.icon.setPixmap(QtGui.QPixmap( \
                    #'/usr/share/icons/oxygen/48x48/status/task-attention.png'))

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
            ## we set /etc/torrc.d/anon_connection_wizard.torrc as 644
            ## so that only root can wirte and read, others can only read,
            ## which prevents the edit by normal user.
            os.chmod(Common.torrc_file_path, 0o644)


        if self.currentId() == self.steps.index('tor_status_page'):
            self.tor_status_page.text.setText('')  # This will clear the text left by different Tor status statement
            if self.tor_status == 'tor_enabled' or self.tor_status == 'tor_already_enabled':
                self.tor_status_page.bootstrap_progress.setVisible(True)

            self.button(QtWidgets.QWizard.BackButton).setVisible(True)
            self.button(QtWidgets.QWizard.CancelButton).setVisible(True)
            self.button(QtWidgets.QWizard.FinishButton).setVisible(False)

            '''Arranging different tor_status_page according to the value of disable_tor.'''
            if not Common.disable_tor:
                # tor_status.set_enabled() does two things:
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
                ## since terminate() should be executed only once,
                ## we should set the flag as False after the execution.
                self.bootstrap_thread = False

                ''' recover Tor to the intial status before the starting of anon_connection_wizard
                '''
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

    def show_finish_button(self):
        if self.bootstrap_done or Common.disable_tor:
            self.button(QtWidgets.QWizard.CancelButton).setVisible(False)
            self.button(QtWidgets.QWizard.FinishButton).setVisible(True)
            self.button(QtWidgets.QWizard.FinishButton).setFocus()

    '''This overrided event handler is called with the given event
    when Qt receives a window close request for a top-level widget from the window system.
    We let it call cancel_button_clicked() to make the consequences of clicking close button
    same with clicking the cancel button.
    '''
    def closeEvent(self, event):
        self.cancel_button_clicked()
        event.accept()  # let the window close

    def io(self):
        repair_torrc.repair_torrc()  # This gurantees a good torrc and the existence of /etc/torrc.d

        # Creates a file and returns a tuple containing both the handle and the path.
        # we are sponsible for removing tmp file when finished which is the reason we use shutil.move(), not shutil.copy(), below
        handle, Common.torrc_tmp_file_path = tempfile.mkstemp()
        with open(handle, "w") as f:
            f.write("\
# This file is generated by and should ONLY be used by anon-connection-wizard.\n\
# User's manual configuration should go to /etc/tor/torrc, not here. Because:\n\
#    1. This file can be easily overwritten by anon-connection-wizard.\n\
#    2. Even a single character change in this file may cause error.\n\
# However, deleting this file will be fine since a new plain file will be generated the next time you run anon-connection-wizard.\n\
")
        
        

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
<<<<<<< HEAD
                    elif Common.bridge_type == 'meek-amazon':
                        f.write(Common.command_meek_lite + '\n')
                    elif Common.bridge_type == 'meek-azure':
                        f.write(Common.command_meek_lite + '\n')
                        # More types of bridges will be availble once Whonix support them: meek, flashproxy
                    elif Common.bridge_type == '':
                        pass
                    bridges = json.loads(open(Common.bridges_default_path).read())
=======
                        # More types of bridges will be availble once Whonix support them: meek, flashproxy
                    elif Common.bridge_type == '':
                        pass
                    bridges = json.loads(open(Common.bridges_default_path).read())  # default bridges will be loaded, however, what does the variable  bridges do? A: for bridge in bridges
>>>>>>> upstream/master
                    for bridge in bridges['bridges'][Common.bridge_type]:  # What does this line mean? A: The bridges are more like a multilayer-dictionary
                        f.write('bridge {0}\n'.format(bridge))  # This is the format to configure a bridge in torrc
                else:  # Use custom bridges
                    f.write(Common.command_use_custom_bridge + '\n')  # mark custom bridges are used
                    
                    if Common.bridge_custom.lower().startswith('obfs4'):
                        f.write(Common.command_obfs4 + '\n')
                    elif Common.bridge_custom.lower().startswith('obfs3'):
                        f.write(Common.command_obfs3 + '\n')
                    elif Common.bridge_custom.lower().startswith('fte'):
                        f.write(Common.command_fte + '\n')
<<<<<<< HEAD
                    elif Common.bridge_custom.lower().startswith('meek_lite'):
                        f.write(Common.command_meek_lite + '\n')
=======
                    elif Common.bridge_custom.lower().startswith('meek-amazon'):
                        pass  # Wait to be implemented in Whonix.
                    elif Common.bridge_custom.lower().startswith('meek-azure'):
                        pass
>>>>>>> upstream/master

                    # Write the specific bridge address, port, cert etc.
                    bridge_custom_list = Common.bridge_custom.split('\n')
                    for bridge in bridge_custom_list:
                        if bridge != '':  # check if the line is actually empty
                            f.write('bridge {0}\n'.format(bridge))


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
<<<<<<< HEAD
                ## This falg is for parsing meek_lite
                use_meek_lite = False
=======
>>>>>>> upstream/master
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
<<<<<<< HEAD
                    elif line.startswith(Common.command_meek_lite):
                        use_meek_lite = True
                    elif use_meek_lite and line.endswith(Common.command_meek_amazon_address):
                        Common.bridge_type = 'meek-amazon (works in China)'
                        Common.bridge_custom += ' '.join(line.split(' ')[1:])  # eliminate the 'Bridge'
                    elif use_meek_lite and line.endswith(Common.command_meek_azure_address):
                        Common.bridge_type = 'meek-azure'
                        Common.bridge_custom += ' '.join(line.split(' ')[1:])  # eliminate the 'Bridge'
=======
>>>>>>> upstream/master
                    elif line.startswith(Common.command_fte):
                        Common.bridge_type = 'fte'
                    elif line.startswith(Common.command_scramblesuit):
                        Common.bridge_type = 'scramblesuit'
                    elif line.startswith(Common.command_bridgeInfo):
                        Common.bridge_custom += ' '.join(line.split(' ')[1:])  # eliminate the 'Bridge'
                    elif line.startswith(Common.command_http):
                        Common.use_proxy = True
                        Common.proxy_type = 'HTTP / HTTPS'
                        ''' Using the following parsing fragments is too fixed,
                        which is not good implementation.
                        But as long as leave .torrc untouched by user, it will be Okay. 
                        We should also be caureful when changing the command line format in this app
                        '''
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
            '''
            bootstrap_status_test = self.tor_controller.get_info("")
            print(bootstrap_status_test)
            '''
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
