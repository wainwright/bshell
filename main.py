#!/usr/bin/python

import sys
import time
import select
import argparse
import threading
from subprocess import *
from collections import deque
from Queue import Queue
from PyQt4 import QtGui, QtCore

class Worker(QtCore.QThread):

	textout = QtCore.pyqtSignal(str)
	runcommand = QtCore.pyqtSignal(str)

	def __init__(self, queue, parent=None, delay=None):
		super(Worker, self).__init__(parent)
		self.queue = queue
		self.delay = delay

	def executeCommand(self, command):
		self.runcommand.emit(command)
		if self.delay: time.sleep(self.delay)
		p = Popen(['bash', '-c', command], stdout=PIPE, stderr=PIPE)
		procFinish = stdoutFinished = stderrFinish = False

		tout = threading.Thread(target=self.readOutput, args=(p.stdout,))
		terr = threading.Thread(target=self.readOutput, args=(p.stderr,))
		tout.start()
		terr.start()
		p.wait()
		tout.join()
		terr.join()

	def readOutput(self, f):
		while True:
			read = f.readline()
			if read == '': break
			self.textout.emit(QtCore.QString.fromUtf8(read))

	def run(self):
		while True:
			cmd = self.queue.get()
			self.executeCommand(cmd)
			self.queue.task_done()

class CommandBufferWindow(QtGui.QPlainTextEdit):

	newCommand = QtCore.pyqtSignal(QtCore.QString)

	def __init__(self, parent=None):
		super(CommandBufferWindow, self).__init__(parent)
		self.resizeLines(0)

	def update(self, entries):
		contents = '\n'.join([str(s) for s in entries]).strip()
		self.setPlainText(contents)
		self.resizeLines(len(entries))

	def resizeLines(self, lines):
		m = QtGui.QFontMetrics(self.font())
		rowHeight = m.lineSpacing()
		fudge = 12
		if lines > 0:
			self.setFixedHeight(rowHeight * lines + fudge)
		else:
			self.setFixedHeight(0)

class CommandBuffer(QtCore.QObject):

	commandAdded = QtCore.pyqtSignal(deque)
	commandTaken = QtCore.pyqtSignal(deque)

	def __init__(self, parent=None):
		super(CommandBuffer, self).__init__(parent)
		self.queue = Queue()

	def put(self, item, block=True, timeout=None):
		self.queue.put(item, block, timeout)
		self.commandAdded.emit(self.queue.queue)

	def get(self, block=True, timeout=None):
		ret = self.queue.get(block, timeout)
		self.commandTaken.emit(self.queue.queue)
		return ret

	def task_done(self):
		self.queue.task_done()

class Main(QtGui.QWidget):

	newCommand = QtCore.pyqtSignal(QtCore.QString)

	def __init__(self, delay=None):
		super(Main, self).__init__()
		self.delay = delay
		self.initUI()

	def initUI(self):
		# the output window
		self.textOut = QtGui.QPlainTextEdit(self)
		self.textOut.setReadOnly(True)
		self.textOut.setFont(QtGui.QFont("UbuntuMono"))

		# the command buffer
		self.cmdBuffer = CommandBuffer(self)
		self.cmdBufferWindow = CommandBufferWindow(self)
		self.cmdBufferWindow.setReadOnly(True)
		self.cmdBufferWindow.setFont(QtGui.QFont("UbuntuMono"))

		# the command editor
		self.linedit = QtGui.QLineEdit(self)
		self.linedit.setFont(QtGui.QFont("UbuntuMono"))
		self.linedit.setFocus()

		# layout
		vbox = QtGui.QVBoxLayout()
		vbox.addWidget(self.textOut)
		vbox.addWidget(self.cmdBufferWindow)
		vbox.addWidget(self.linedit)
		self.setLayout(vbox)

		# start thread and connect everything up
		self.worker = Worker(self.cmdBuffer, delay=self.delay)
		self.worker.start()

		self.linedit.returnPressed.connect(self._processCommand)
		self.linedit.returnPressed.connect(self.linedit.clear)
		self.worker.runcommand.connect(self.printCommand)
		self.newCommand.connect(self.cmdBuffer.put)
		self.cmdBuffer.commandAdded.connect(self.cmdBufferWindow.update)
		self.cmdBuffer.commandTaken.connect(self.cmdBufferWindow.update)
		self.worker.textout.connect(self.printOutput)

		self.setGeometry(300, 300, 680, 700)
		self.setWindowTitle('bshell')
		self.show()

	def _processCommand(self):
		self.newCommand.emit(self.linedit.text())

	def printCommand(self, command):
		self.printOutput('> ' + command + '\n')

	def printOutput(self, output):
		self.textOut.moveCursor(QtGui.QTextCursor.End)
		self.textOut.textCursor().insertText(output)

def main():
	parser = argparse.ArgumentParser(description='Buffered shell')
	parser.add_argument('--delay', type=int,
		help='artificial processing delay for testing the buffer')
	args = parser.parse_args()
	app = QtGui.QApplication(sys.argv)
	ex = Main(delay=args.delay)
	sys.exit(app.exec_())

if __name__ == '__main__':
	main()
