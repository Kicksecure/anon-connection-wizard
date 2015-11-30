#!/usr/bin/python
# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui
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
import tor_status


class Common:
    '''
    Variables and constants used through all the classes
    '''
    translations_path ='/usr/share/translations/whonix_setup.yaml'

    bridges_default_path = '/usr/share/whonix-setup-wizard/bridges_default'
    use_bridges = False
    use_proxy = False
    bridge_type = ''
    disable_tor = False

    if not os.path.exists('/var/cache/whonix-setup-wizard/status-files/whonix_connection.done'):
        ## "not whonix_connection.done" is required once at first run to get a copy of the original torrc.
        ## It does not matter whether the wizard is completed or not, so we can write it here.
        f = open('/var/cache/whonix-setup-wizard/status-files/whonix_connection.done', 'w')
        f.close()
        shutil.copy('/etc/tor/torrc', '/etc/tor/torrc.orig')

    if not os.path.exists('/var/cache/whonix-setup-wizard/status-files'):
        os.mkdir('/var/cache/whonix-setup-wizard/status-files')

    wizard_steps = ['connection_main_page',
                    'bridge_wizard_page_1',
                    'bridge_wizard_page_2',
                    'proxy_wizard_page_1',
                    'proxy_wizard_page_2',
                    'tor_status_page']


class ConnectionMainPage(QtGui.QWizardPage):
    def __init__(self):
        super(ConnectionMainPage, self).__init__()

        self.steps = Common.wizard_steps

        self.verticalLayout = QtGui.QVBoxLayout(self)
        self.groupBox = QtGui.QGroupBox(self)
        self.label = QtGui.QLabel(self.groupBox)
        self.label_2 = QtGui.QLabel(self.groupBox)
        self.pushButton_1 = QtGui.QRadioButton(self.groupBox)
        self.label_4 = QtGui.QLabel(self.groupBox)
        self.pushButton_2 = QtGui.QRadioButton(self.groupBox)
        self.label_5 = QtGui.QLabel(self.groupBox)
        self.pushButton_3 = QtGui.QRadioButton(self.groupBox)

        self.pushButton = QtGui.QPushButton(self.groupBox)
        self.show_disable = False

        self.verticalLayout.addWidget(self.groupBox)

        self.setupUi()

    def setupUi(self):
        self.groupBox.setFlat(True)
        self.groupBox.setMinimumSize(QtCore.QSize(500, 320))

        self.label.setGeometry(QtCore.QRect(20, 0, 510, 41))
        self.label.setWordWrap(True)
        self.label.setText('Before you connect to the Tor network, you need to provide information about this computer Internet connection.')

        self.label_2.setGeometry(QtCore.QRect(10, 60, 431, 21))
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.label_2.setFont(font)
        self.label_2.setText('Which of the following best describes your situation?')

        self.label_3 = QtGui.QLabel(self.groupBox)
        self.label_3.setGeometry(QtCore.QRect(10, 85, 321, 41))
        self.label_3.setWordWrap(True)
        self.label_3.setText('I would like to connect directly to the Tor netwotk. This will work in most situations.')

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
        self.pushButton_3.setVisible(False)

        self.label_4.setGeometry(QtCore.QRect(10, 165, 381, 41))
        self.label_4.setWordWrap(True)
        self.label_4.setText('This computer\'s Internet connection is censored or proxied. I need to configure bridges or local proxy settings.')

        self.label_5.setGeometry(QtCore.QRect(10, 250, 500, 31))
        self.label_5.setWordWrap(True)
        self.label_5.setText('I do not want to connect automatically to the Tor network next time I boot.<br> This wizard will be started.')
        self.label_5.setVisible(False)

        self.pushButton.setGeometry(QtCore.QRect(453, 285, 80, 25))
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

    def nextId(self):
        if self.pushButton_1.isChecked():
            Common.disable_tor = False
            return self.steps.index('tor_status_page')
        elif self.pushButton_2.isChecked():
            Common.disable_tor = False
            return self.steps.index('bridge_wizard_page_1')
        elif self.pushButton_3.isChecked():
            Common.disable_tor = True
            return self.steps.index('tor_status_page')


class BridgesWizardPage1(QtGui.QWizardPage):
    def __init__(self):
        super(BridgesWizardPage1, self).__init__()

        translation = _translations(Common.translations_path, 'whonixsetup')
        self._ = translation.gettext

        self.steps = Common.wizard_steps

        self.layout = QtGui.QVBoxLayout(self)
        self.label = QtGui.QLabel(self)
        self.layout.addWidget(self.label)

        self.label_2 = QtGui.QLabel(self)
        self.layout.addWidget(self.label_2)

        self.group_box = QtGui.QGroupBox(self)
        self.yes_button = QtGui.QRadioButton(self.group_box)
        self.no_button = QtGui.QRadioButton(self.group_box)
        self.label_3 = QtGui.QLabel(self.group_box)
        self.label_4 = QtGui.QLabel(self.group_box)
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
        self.label_2.setText('Does your Internet Service Provider (ISP) block or otherwise censor connections to the Tor network?')

        self.group_box.setMinimumSize(QtCore.QSize(16777215, 244))
        self.group_box.setFlat(True)
        self.yes_button.setGeometry(QtCore.QRect(25, 0, 350, 21))
        self.yes_button.setText('Yes')
        self.no_button.setGeometry(QtCore.QRect(25, 20, 350, 21))
        self.no_button.setText('No')
        self.no_button.setChecked(True)

        #self.label_3.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.label_3.setGeometry(10, 55, 520, 60)
        self.label_3.setTextFormat(QtCore.Qt.RichText)
        self.label_3.setWordWrap(True)
        self.label_3.setText('If you are not sure how to answer this question, choose No. \
            If you choose Yes, you will be asked to configure Tor bridges, \
            which are unlisted relays that make it more difficult to block connections \
            to the Tor network.')

        self.label_4.setGeometry(0, 220, 500, 15)
        self.label_4.setText('For assistance, contact help@rt.torproject.org')

    def nextId(self):
        if self.yes_button.isChecked():
            Common.use_bridges = True
            return self.steps.index('bridge_wizard_page_2')
        elif self.no_button.isChecked():
            Common.use_bridges = False
            return self.steps.index('proxy_wizard_page_1')


class BridgesWizardPage2(QtGui.QWizardPage):
    def __init__(self):
        super(BridgesWizardPage2, self).__init__()

        self.steps = Common.wizard_steps

        self.bridges = ['obfs3 (recommended)',
                        'obfs4',
                        'scramblesuit']

        self.layout = QtGui.QVBoxLayout(self)
        self.label = QtGui.QLabel(self)
        self.layout.addWidget(self.label)

        self.label_2 = QtGui.QLabel(self)
        self.layout.addWidget(self.label_2)

        self.groupBox = QtGui.QGroupBox(self)
        self.default_button = QtGui.QRadioButton(self.groupBox)
        self.custom_button = QtGui.QRadioButton(self.groupBox)
        self.label_3 = QtGui.QLabel(self.groupBox)
        self.comboBox = QtGui.QComboBox(self.groupBox)
        self.label_4 = QtGui.QLabel(self.groupBox)
        self.custom_bridges = QtGui.QTextEdit(self.groupBox)
        self.pushButton = QtGui.QPushButton(self.groupBox)
        self.label_5 = QtGui.QLabel(self.groupBox)

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
        self.label_2.setText('You may use the provided set of briges or you may obtain and enter a custom set of bridges.')

        self.groupBox.setMinimumSize(QtCore.QSize(16777215, 243))
        self.groupBox.setFlat(True)
        self.default_button.setGeometry(QtCore.QRect(18, 3, 500, 24))
        self.default_button.setChecked(True)
        self.default_button.setText('Connect with provided bridges')

        self.custom_button.setGeometry(QtCore.QRect(18, 60, 500, 25))
        self.custom_button.setText('Enter custom bridges')

        self.label_3.setGeometry(QtCore.QRect(38, 25, 106, 20))
        self.label_3.setText('Transport type:')

        self.comboBox.setGeometry(QtCore.QRect(135, 22, 181, 27))
        for bridge in self.bridges:
            self.comboBox.addItem(bridge)

        self.label_4.setEnabled(False)
        self.label_4.setGeometry(QtCore.QRect(38, 83, 300, 20))
        self.label_4.setText('Enter one ore more bridge relay (one per line).')

        self.pushButton.setGeometry(QtCore.QRect(450, 70, 86, 25))
        self.pushButton.setText('&Help')
        self.pushButton.clicked.connect(self.show_help)

        self.custom_bridges.setEnabled(False)
        self.custom_bridges.setGeometry(QtCore.QRect(38, 103, 500, 76))
        self.custom_bridges.setStyleSheet("background-color:white;")

        self.label_5.setGeometry(0, 220, 500, 15)
        self.label_5.setText('For assistance, contact help@rt.torproject.org')

    def nextId(self):
        if self.default_button.isChecked():
            bridge_type = str(self.comboBox.currentText())
            if bridge_type.startswith('obfs3'):
                bridge_type = 'obfs3'
            Common.bridge_type = bridge_type

        elif self.custom_button.isChecked():
            pass

        return self.steps.index('proxy_wizard_page_1')

    def show_help(self):
        reply = QtGui.QMessageBox(QtGui.QMessageBox.NoIcon, 'Bridges Configuration Help',
                                  '''<p><b>  Bridge Relay Help</b></p>

<p>If you are unable to connect to the Tor network, it could be that your Internet Service
Provider (ISP) or another agency is blocking Tor.  Often, you can work around this problem
by using Tor Bridges, which are unlisted relays that are more difficult to block.</p>

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
to each request.</blockquote>''', QtGui.QMessageBox.Ok)
        reply.exec_()


class ProxyWizardPage1(QtGui.QWizardPage):
    def __init__(self):
        super(ProxyWizardPage1, self).__init__()

        translation = _translations(Common.translations_path, 'whonixsetup')
        self._ = translation.gettext

        self.Common = Common()
        self.steps = self.Common.wizard_steps

        self.layout = QtGui.QVBoxLayout(self)
        self.label = QtGui.QLabel(self)
        self.layout.addWidget(self.label)

        self.label_2 = QtGui.QLabel(self)
        self.layout.addWidget(self.label_2)

        self.group_box = QtGui.QGroupBox(self)
        self.yes_button = QtGui.QRadioButton(self.group_box)
        self.no_button = QtGui.QRadioButton(self.group_box)
        self.label_3 = QtGui.QLabel(self.group_box)
        self.label_4 = QtGui.QLabel(self.group_box)
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
        self.label_2.setText('Does this computer need tot use a local proxy to access the Internet?')

        self.group_box.setMinimumSize(QtCore.QSize(16777215, 250))
        self.group_box.setFlat(True)
        self.yes_button.setGeometry(QtCore.QRect(25, 0, 350, 21))
        self.yes_button.setText('Yes')
        self.no_button.setGeometry(QtCore.QRect(25, 20, 350, 21))
        self.no_button.setText('No')
        self.no_button.setChecked(True)

        #self.label_3.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.label_3.setGeometry(10, 45, 520, 60)
        self.label_3.setTextFormat(QtCore.Qt.RichText)
        self.label_3.setWordWrap(True)
        self.label_3.setText('If you are not sure how to answer this question, look at the Internet \
                              settings in your host browser to see wether it is configured to use \
                              a local proxy')

        self.label_4.setGeometry(0, 235, 500, 15)
        self.label_4.setText('For assistance, contact help@rt.torproject.org')

    def nextId(self):
        if self.yes_button.isChecked():
            Common.use_proxy = True
            return self.steps.index('proxy_wizard_page_2')
        elif self.no_button.isChecked():
            Common.use_proxy = False
            return self.steps.index('tor_status_page')


class ProxyWizardPage2(QtGui.QWizardPage):
    def __init__(self):
        super(ProxyWizardPage2, self).__init__()

        Common.use_proxy = True
        translation = _translations(Common.translations_path, 'whonixsetup')
        self._ = translation.gettext
        self.steps = Common.wizard_steps

        self.layout = QtGui.QVBoxLayout(self)
        self.label = QtGui.QLabel(self)
        self.layout.addWidget(self.label)

        self.groupBox = QtGui.QGroupBox(self)
        self.label_3 = QtGui.QLabel(self.groupBox)
        self.comboBox = QtGui.QComboBox(self.groupBox)
        self.label_2 = QtGui.QLabel(self.groupBox)
        self.label_5 = QtGui.QLabel(self.groupBox)
        self.label_6 = QtGui.QLabel(self.groupBox)
        self.lineEdit = QtGui.QLineEdit(self.groupBox)
        self.label_7 = QtGui.QLabel(self.groupBox)
        self.lineEdit_2 = QtGui.QLineEdit(self.groupBox)
        self.lineEdit_3 = QtGui.QLineEdit(self.groupBox)
        self.lineEdit_4 = QtGui.QLineEdit(self.groupBox)
        self.label_8 = QtGui.QLabel(self.groupBox)
        self.label_4 = QtGui.QLabel(self.groupBox)
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

        self.label_3.setGeometry(QtCore.QRect(10, 40, 106, 20))
        self.label_3.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_3.setText("Proxy type:")

        self.comboBox.setGeometry(QtCore.QRect(118, 38, 111, 27))

        self.label_2.setGeometry(QtCore.QRect(4, 10, 201, 16))
        self.label_2.setText("Enter the proxy settings.")

        self.label_5.setGeometry(QtCore.QRect(10, 71, 106, 20))
        self.label_5.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_5.setText("Address:")

        self.label_6.setGeometry(QtCore.QRect(10, 101, 106, 20))
        self.label_6.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_6.setText("Username:")

        self.label_7.setGeometry(QtCore.QRect(394, 71, 41, 20))
        self.label_7.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_7.setText("Port:")

        self.label_8.setGeometry(QtCore.QRect(280, 101, 70, 20))
        self.label_8.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_8.setText("Password:")

        self.lineEdit.setGeometry(QtCore.QRect(118, 68, 260, 25))
        self.lineEdit.setStyleSheet("background-color:white;")
        self.lineEdit.setPlaceholderText('IP address or hostname')
        self.lineEdit_2.setGeometry(QtCore.QRect(437, 68, 60, 25))
        self.lineEdit_2.setStyleSheet("background-color:white;")
        self.lineEdit_3.setGeometry(QtCore.QRect(118, 98, 150, 25))
        self.lineEdit_3.setStyleSheet("background-color:white;")
        self.lineEdit_3.setPlaceholderText('Optional')
        self.lineEdit_4.setGeometry(QtCore.QRect(352, 98, 145, 25))
        self.lineEdit_4.setStyleSheet("background-color:white;")
        self.lineEdit_4.setPlaceholderText('Optional')

        self.label_4.setGeometry(QtCore.QRect(0, 255, 391, 16))
        self.label_4.setText("For assistance, contact help@rt.torproject.org'")


class TorStatusPage(QtGui.QWizardPage):
    def __init__(self):
        super(TorStatusPage, self).__init__()

        self.steps = Common.wizard_steps

        #self.icon = QtGui.QLabel(self)
        self.bootstrap_text = QtGui.QLabel(self)
        self.text = QtGui.QLabel(self)
        #self.torrc = QtGui.QPlainTextEdit(self)
        self.bootstrap_progress = QtGui.QProgressBar(self)

        self.layout = QtGui.QGridLayout()
        self.setupUi()

    def setupUi(self):
        #self.text.setFrameShape(QtGui.QFrame.NoFrame)
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

app = QtGui.QApplication(sys.argv)


class WhonixConnectionWizard(QtGui.QWizard):
    def __init__(self):
        super(WhonixConnectionWizard, self).__init__()

        translation = _translations(Common.translations_path, 'whonixsetup')
        self._ = translation.gettext

        self.steps = Common.wizard_steps

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
        self.tor_status_page = TorStatusPage()
        self.addPage(self.tor_status_page)

        #self.bootstrap_thread = TorBootstrap(self)
        #self.bootstrap_thread.finished.connect(app.exit)
        #self.connect(self.bootstrap_thread, self.bootstrap_thread.signal, self.update_bootstrap)
        self.bridges = []
        self.proxy_type = ''
        self.tor_status = ''
        self.bootstrap_done = False

        self.setupUi()

    def setupUi(self):
        self.setWindowIcon(QtGui.QIcon("/usr/share/icons/anon-icon-pack/whonix.ico"))
        self.setWindowTitle('Whonix Connection Wizard')
        self.resize(580, 400)

        self.button(QtGui.QWizard.BackButton).clicked.connect(self.back_button_clicked)
        self.button(QtGui.QWizard.NextButton).clicked.connect(self.next_button_clicked)

        self.button(QtGui.QWizard.BackButton).setVisible(False)
        self.CancelButtonOnLeft
        self.button(QtGui.QWizard.CancelButton).setVisible(True)
        self.button(QtGui.QWizard.CancelButton).setEnabled(True)
        #self.button(QtGui.QWizard.CancelButton).setFocus()
        self.button(QtGui.QWizard.CancelButton).clicked.connect(self.cancel_button_clicked)
        self.exec_()


    def update_bootstrap(self, status):
        if status != 'timeout':
            bootstrap_phase = re.search(r'SUMMARY=(.*)', status).group(1)
            bootstrap_percent = int(re.match('.* PROGRESS=([0-9]+).*', status).group(1))
            if bootstrap_percent == 100:
                self.tor_status_page.text.setText('<p><b>Tor bootstrapping done</b></p>Bootstrap phase: %s' % bootstrap_phase)
                self.bootstrap_done = True
            else:
                self.tor_status_page.text.setText('<p><b>Bootstrapping Tor...</b></p>Bootstrap phase: %s' % bootstrap_phase)
            self.tor_status_page.bootstrap_progress.setValue(bootstrap_percent)
        else:
            self.bootstrap_timeout = True

    def cancel_button_clicked(self):
        try:
            if self.bootstrap_thread:
                self.bootstrap_thread.terminate()
        except AttributeError:
            pass

    def next_button_clicked(self):
        """
        """
        if self.currentId() == self.steps.index('connection_main_page'):
            self.resize(580, 400)
            self.button(QtGui.QWizard.CancelButton).setVisible(True)
            self.button(QtGui.QWizard.FinishButton).setVisible(False)
            #self.center()

        if self.currentId() == self.steps.index('tor_status_page'):
            self.button(QtGui.QWizard.BackButton).setVisible(True)
            self.button(QtGui.QWizard.CancelButton).setVisible(True)
            self.button(QtGui.QWizard.FinishButton).setVisible(False)
            ## Get a fresh torrc
            shutil.copy('/etc/tor/torrc.orig', '/etc/tor/torrc')

            if Common.use_bridges:
                bridges = json.loads(open(Common.bridges_default_path).read())
                with open('/etc/tor/torrc', 'a') as f:
                    f.write('UseBridges 1\n')

                    if Common.bridge_type == 'obfs3':
                        f.write('ClientTransportPlugin obfs2,obfs3 exec /usr/bin/obfsproxy managed\n')
                    elif Common.bridge_type == 'scramblesuit':
                        f.write('ClientTransportPlugin obfs2,obfs3,scramblesuit exec /usr/bin/obfsproxy managed\n')
                    elif Common.bridge_type == 'obfs4':
                        f.write('ClientTransportPlugin obfs4 exec /usr/bin/obfs4proxy managed\n')

                    for bridge in bridges['bridges'][Common.bridge_type]:
                        f.write('Bridge %s\n' % bridge)

            if Common.use_proxy:
                pass

            if not Common.disable_tor:
                self.tor_status = tor_status.set_enabled()
            else:
                self.tor_status = tor_status.set_disabled()

            if self.tor_status == 'tor_enabled' or self.tor_status == 'tor_already_enabled':
                self.tor_status_page.bootstrap_progress.setVisible(True)
                self.bootstrap_thread = TorBootstrap(self)
                self.connect(self.bootstrap_thread, self.bootstrap_thread.signal, self.update_bootstrap)
                self.bootstrap_thread.finished.connect(self.finish)
                self.bootstrap_thread.start()

            elif self.tor_status == 'tor_disabled':
                self.tor_status_page.bootstrap_progress.setVisible(False)
                self.tor_status_page.text.setText('<b>Tor is disabled.</b> You will not be able to use any \
                                                   network facing application.<p> If you shut down the gateway \
                                                   now, this wizard will be run automatically next time you boot. \
                                                   </p><p>You can run it at any moment using <i>Anon Connection Wizard</i> \
                                                   from your application launcher, or from a terminal:<blockquote> \
                                                   <code>kdesudo anon-connection-wizard</code></blockquote> \
                                                   or press the Back button and select another option.')


    def back_button_clicked(self):
        try:
            if self.bootstrap_thread:
                self.bootstrap_thread.terminate()
        except AttributeError:
            pass

        if self.currentId() == self.steps.index('connection_main_page'):
            Common.use_bridges = False
            shutil.copy('/etc/tor/torrc.orig', '/etc/tor/torrc')
            self.bootstrap_done = False
            self.button(QtGui.QWizard.FinishButton).setVisible(False)
            self.button(QtGui.QWizard.CancelButton).setVisible(True)

        if self.currentId() == self.steps.index('proxy_wizard_page_1'):
            self.bootstrap_done = False
            self.button(QtGui.QWizard.FinishButton).setVisible(False)
            self.button(QtGui.QWizard.CancelButton).setVisible(True)

    def finish(self):
        if self.bootstrap_done:
            self.button(QtGui.QWizard.CancelButton).setVisible(False)
            self.button(QtGui.QWizard.FinishButton).setVisible(True)
            self.button(QtGui.QWizard.FinishButton).setFocus()


class TorBootstrap(QtCore.QThread):
    def __init__(self, main):
        from stem.connection import connect
        #super(TorBootstrap, self).__init__(main)
        QtCore.QThread.__init__(self, parent=None)
        self.controller = connect()
        self.signal = QtCore.SIGNAL("signal")
        self.previous_status = ''
        self.bootstrap_percent = 0
        #self.is_running = False

    def run(self):
        #self.is_running = True
        while self.bootstrap_percent < 100:
            bootstrap_status = self.controller.get_info("status/bootstrap-phase")
            self.bootstrap_percent = int(re.match('.* PROGRESS=([0-9]+).*', bootstrap_status).group(1))
            if bootstrap_status != self.previous_status:
                sys.stdout.write('%s\n' % bootstrap_status)
                sys.stdout.flush()
                self.previous_status = bootstrap_status
                self.emit(self.signal, bootstrap_status)
            time.sleep(0.2)

def main():
    QtGui.QApplication.setStyle('cleanlooks')
    # root check.
    if os.getuid() != 0:
        print 'ERROR: This must be run as root!\nUse "kdesudo".'
        not_root = gui_message(Common.translations_path, 'not_root')
        sys.exit(1)
    wizard = WhonixConnectionWizard()

    sys.exit(0)

if __name__ == "__main__":
    main()
