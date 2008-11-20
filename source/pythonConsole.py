"""Provides an interactive Python console which can be run from within NVDA.
To use, call L{initialize} to create a singleton instance of the console GUI. This can then be accessed externally as L{consoleUI}.
"""

import __builtin__
import code
import sys
import wx
from baseObject import AutoPropertyObject
import speech
import queueHandler
import api
import gui
from logHandler import log
import braille

#: The singleton Python console UI instance.
consoleUI = None

class PythonConsole(code.InteractiveConsole, AutoPropertyObject):
	"""An interactive Python console which directs output to supplied functions.
	This is necessary for a Python console facilitated by a GUI.
	Input is always received via the L{push} method.
	This console also handles redirection of stdout and stderr and prevents clobbering of the gettext "_" builtin.
	"""

	def __init__(self, outputFunc, echoFunc, setPromptFunc, **kwargs):
		# Can't use super here because stupid code.InteractiveConsole doesn't sub-class object. Grrr!
		code.InteractiveConsole.__init__(self, **kwargs)
		self._output = outputFunc
		self._echo = echoFunc
		self._setPrompt = setPromptFunc
		self.prompt = ">>>"

	def _set_prompt(self, prompt):
		self._prompt = prompt
		self._setPrompt(prompt)

	def _get_prompt(self):
		return self._prompt

	def write(self, data):
		self._output(data)

	def push(self, line):
		self._echo("%s %s\n" % (self.prompt, line))
		# Capture stdout/stderr output as well as code interaction.
		stdout, stderr = sys.stdout, sys.stderr
		sys.stdout = sys.stderr = self
		# Prevent this from messing with the gettext "_" builtin.
		saved_ = __builtin__._
		more = code.InteractiveConsole.push(self, line)
		sys.stdout, sys.stderr = stdout, stderr
		__builtin__._ = saved_
		self.prompt = "..." if more else ">>>"
		return more

class ConsoleUI(wx.Frame):
	"""The NVDA Python console GUI.
	"""

	def __init__(self, parent):
		super(ConsoleUI, self).__init__(parent, wx.ID_ANY, _("NVDA Python Console"))
		self.Bind(wx.EVT_ACTIVATE, self.onActivate)
		self.Bind(wx.EVT_CLOSE, self.onClose)
		mainSizer = wx.BoxSizer(wx.VERTICAL)
		self.outputCtrl = wx.TextCtrl(self, wx.ID_ANY, size=(500, 500), style=wx.TE_MULTILINE | wx.TE_READONLY|wx.TE_RICH)
		self.outputCtrl.Bind(wx.EVT_CHAR, self.onOutputChar)
		mainSizer.Add(self.outputCtrl, proportion=2, flag=wx.EXPAND)
		inputSizer = wx.BoxSizer(wx.HORIZONTAL)
		self.promptLabel = wx.StaticText(self, wx.ID_ANY)
		inputSizer.Add(self.promptLabel, flag=wx.EXPAND)
		self.inputCtrl = wx.TextCtrl(self, wx.ID_ANY, style=wx.TE_DONTWRAP | wx.TE_PROCESS_TAB)
		self.inputCtrl.Bind(wx.EVT_CHAR, self.onInputChar)
		inputSizer.Add(self.inputCtrl, proportion=1, flag=wx.EXPAND)
		mainSizer.Add(inputSizer, proportion=1, flag=wx.EXPAND)
		self.SetSizer(mainSizer)
		mainSizer.Fit(self)

		#: The namespace available to the console. This can be updated externally.
		#: @type: dict
		self.namespace = {}
		self.console = PythonConsole(outputFunc=self.output, echoFunc=self.echo, setPromptFunc=self.setPrompt, locals=self.namespace)
		# Even the most recent line has a position in the history, so initialise with one blank line.
		self.inputHistory = [""]
		self.inputHistoryPos = 0

	def onActivate(self, evt):
		if evt.GetActive():
			self.inputCtrl.SetFocus()
		evt.Skip()

	def onClose(self, evt):
		self.Hide()

	def output(self, data):
		self.outputCtrl.write(data)
		if data and not data.isspace():
			queueHandler.queueFunction(queueHandler.eventQueue, speech.speakText, data)

	def echo(self, data):
		self.outputCtrl.write(data)

	def setPrompt(self, prompt):
		self.promptLabel.SetLabel(prompt)
		queueHandler.queueFunction(queueHandler.eventQueue, speech.speakText, prompt)

	def execute(self):
		data = self.inputCtrl.GetValue()
		self.console.push(data)
		if data:
			# Only add non-blank lines to history.
			if len(self.inputHistory) > 1 and self.inputHistory[-2] == data:
				# The previous line was the same and we don't want consecutive duplicates, so trash the most recent line.
				del self.inputHistory[-1]
			else:
				# Update the content for the most recent line of history.
				self.inputHistory[-1] = data
			# Start with a new, blank line.
			self.inputHistory.append("")
		self.inputHistoryPos = len(self.inputHistory) - 1
		self.inputCtrl.ChangeValue("")

	def historyMove(self, movement):
		newIndex = self.inputHistoryPos + movement
		if not (0 <= newIndex < len(self.inputHistory)):
			# No more lines in this direction.
			return False
		# Update the content of the history at the current position.
		self.inputHistory[self.inputHistoryPos] = self.inputCtrl.GetValue()
		self.inputHistoryPos = newIndex
		self.inputCtrl.ChangeValue(self.inputHistory[newIndex])
		self.inputCtrl.SetInsertionPointEnd()
		return True

	def onInputChar(self, evt):
		key = evt.GetKeyCode()
		if key == wx.WXK_RETURN:
			self.execute()
			return
		elif key in (wx.WXK_UP, wx.WXK_DOWN):
			if self.historyMove(-1 if key == wx.WXK_UP else 1):
				return
		elif key == wx.WXK_F6:
			self.outputCtrl.SetFocus()
			return
		evt.Skip()

	def onOutputChar(self, evt):
		key = evt.GetKeyCode()
		if key == wx.WXK_F6:
			self.inputCtrl.SetFocus()
			return
		evt.Skip()

	def updateNamespaceSnapshotVars(self):
		"""Update the console namespace with a snapshot of NVDA's current state.
		This creates/updates variables for the current focus, navigator object, etc.
		"""
		self.namespace.update({
			"focus": api.getFocusObject(),
			# Copy the focus ancestor list, as it gets mutated once it is replaced in api.setFocusObject.
			"focusAnc": list(api.getFocusAncestors()),
			"fdl": api.getFocusDifferenceLevel(),
			"fg": api.getForegroundObject(),
			"nav": api.getNavigatorObject(),
			"mouse": api.getMouseObject(),
			"log": log,
			"queueHandler": queueHandler,
			"speech": speech,
			"braille": braille,
		})

def initialize():
	"""Initialize the NVDA Python console GUI.
	This creates a singleton instance of the console GUI. This is accessible as L{consoleUI}. This may be manipulated externally.
	"""
	global consoleUI
	consoleUI = ConsoleUI(gui.mainFrame)

def activate():
	"""Activate the console GUI.
	This shows the GUI and brings it to the foreground if possible.
	@precondition: L{initialize} has been called.
	"""
	global consoleUI
	consoleUI.Raise()
	consoleUI.Show()
