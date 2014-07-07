#!/usr/bin/python

import time
import sys
from subprocess import *
from PyQt4 import QtGui, QtCore

class Main(QtGui.QWidget):
	newCommand = QtCore.pyqtSignal(QtCore.QString)

	def __init__(self):
		super(Main, self).__init__()
		self.initUI()

	def initUI(self):
		self.textOut = QtGui.QPlainTextEdit(self)
		self.textOut.setReadOnly(True)
		self.textOut.setFont(QtGui.QFont("UbuntuMono"))
		self.linedit = QtGui.QLineEdit(self)
		self.linedit.setFont(QtGui.QFont("UbuntuMono"))
		self.linedit.setFocus()

		vbox = QtGui.QVBoxLayout()
		vbox.addWidget(self.textOut)
		vbox.addWidget(self.linedit)
		self.setLayout(vbox)

		self.linedit.returnPressed.connect(self._processCommand)
		self.newCommand.connect(self.printCommand)
		self.newCommand.connect(self.executeCommand)

		self.setGeometry(300, 300, 680, 700)
		self.setWindowTitle('bshell')
		self.show()

	def _processCommand(self):
		self.newCommand.emit(self.linedit.text())

	def printCommand(self, command):
		# print the command
		self.textOut.appendPlainText('> ' + command)
		self.linedit.clear()

	def executeCommand(self, command):
		# execute
		p = Popen(['bash', '-c', command], stdout=PIPE)
		output = p.communicate()[0]
		decodedOutput = output.decode('utf-8')
		self.textOut.appendPlainText(decodedOutput)


def main():

	app = QtGui.QApplication(sys.argv)
	ex = Main()
	sys.exit(app.exec_())


if __name__ == '__main__':
	main()
