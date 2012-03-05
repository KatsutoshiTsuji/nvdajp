#updateCheck.py
#A part of NonVisual Desktop Access (NVDA)
#This file is covered by the GNU General Public License.
#See the file COPYING for more details.
#Copyright (C) 2012 NV Access Limited

"""Update checking functionality.
@note: This module may raise C{RuntimeError} on import if update checking for this build is not supported.
"""

import versionInfo
if not versionInfo.updateVersionType:
	raise RuntimeError("No update version type, update checking not supported")

import sys
import os
import threading
import time
import urllib
import wx
import languageHandler
import gui
from logHandler import log
import config

#: The URL to use for update checks.
CHECK_URL = "http://www.nvda-project.org/updateCheck"
#: The time to wait between checks.
CHECK_INTERVAL = 86400 # 1 day
#: The time to wait before retrying a failed check.
RETRY_INTERVAL = 600 # 10 min

# FIXME
state = {
	"lastCheck": 0,
	"dontRemindVersion": None,
}

#: The single instance of L{AutoUpdateChecker} if automatic update checking is enabled,
#: C{None} if it is disabled.
autoChecker = None

def checkForUpdate(auto=False):
	"""Check for an updated version of NVDA.
	This will block, so it generally shouldn't be called from the main thread.
	@param auto: Whether this is an automatic check for updates.
	@type auto: bool
	@return: Information about the update or C{None} if there is no update.
	@rtype: dict
	@raise RuntimeError: If there is an error checking for an update.
	"""
	winVer = sys.getwindowsversion()
	params = {
		"autoCheck": auto,
		"version": versionInfo.version,
		"versionType": versionInfo.updateVersionType,
		"osVersion": "{v.major}.{v.minor}.{v.build} {v.service_pack}".format(v=winVer),
		"x64": os.environ.get("PROCESSOR_ARCHITEW6432") == "AMD64",
		"language": languageHandler.getLanguage(),
	}
	res = urllib.urlopen("%s?%s" % (CHECK_URL, urllib.urlencode(params)))
	if res.code != 200:
		raise RuntimeError("Checking for update failed with code %d" % res.code)
	info = {}
	for line in res:
		line = line.rstrip()
		try:
			key, val = line.split(": ", 1)
		except ValueError:
			raise RuntimeError("Error in update check output")
		info[key] = val
	if not info:
		return None
	return info

class UpdateChecker(object):
	"""Check for an updated version of NVDA, presenting appropriate user interface.
	The check is performed in the background.
	This class is for manual update checks.
	To use, call L{check} on an instance.
	"""
	AUTO = False

	def check(self):
		"""Check for an update.
		"""
		t = threading.Thread(target=self._bg)
		t.daemon = True
		t.start()

	def _bg(self):
		try:
			info = checkForUpdate(self.AUTO)
		except:
			log.debugWarning("Error checking for update", exc_info=True)
			self._error()
			return
		self._result(info)
		if info:
			state["dontRemindVersion"] = info["version"]
		state["lastCheck"] = time.time()
		if autoChecker:
			autoChecker.setNextCheck()

	def _error(self):
		wx.CallAfter(gui.messageBox,
			# Translators: A message indicating that an error occurred while checking for an update to NVDA.
			_("Error checking for update."),
			# Translators: The title of an error message dialog.
			_("Error"),
			wx.OK | wx.ICON_ERROR)

	def _result(self, info):
		wx.CallAfter(UpdateResultDialog, gui.mainFrame, info, False)

class AutoUpdateChecker(UpdateChecker):
	"""Automatically check for an updated version of NVDA.
	To use, create a single instance and maintain a reference to it.
	Checks will then be performed automatically.
	"""
	AUTO = True

	def __init__(self):
		self._checkTimer = wx.PyTimer(self.check)
		# Set the initial check based on the last check time.
		secs = CHECK_INTERVAL - int(min(time.time() - state["lastCheck"], CHECK_INTERVAL))
		self._checkTimer.Start(secs * 1000, True)

	def setNextCheck(self, isRetry=False):
		self._checkTimer.Stop()
		self._checkTimer.Start((RETRY_INTERVAL if isRetry else CHECK_INTERVAL) * 1000, True)

	def _error(self):
		self.setNextCheck(isRetry=True)

	def _result(self, info):
		if not info:
			return
		if info["version"] == state["dontRemindVersion"]:
			return
		wx.CallAfter(UpdateResultDialog, gui.mainFrame, info, True)

class UpdateResultDialog(wx.Dialog):

	def __init__(self, parent, updateInfo, auto):
		# Translators: The title of the dialog informing the user about an NVDA update.
		super(UpdateResultDialog, self).__init__(parent, title=_("NVDA Update"))
		self.updateInfo = updateInfo
		mainSizer = wx.BoxSizer(wx.VERTICAL)

		if updateInfo:
			# Translators: A message indicating that an updated version of NVDA is available.
			# {version} will be replaced with the version; e.g. 2011.3.
			message = _("NVDA version {version} is available.").format(**updateInfo)
		else:
			# Translators: A message indicating that no update to NVDA is available.
			message = _("No update available.")
		mainSizer.Add(wx.StaticText(self, label=message))

		if updateInfo:
			# Translators: The label of a button to download an NVDA update.
			item = wx.Button(self, label=_("&Download update"))
			item.Bind(wx.EVT_BUTTON, self.onDownloadButton)
			mainSizer.Add(item)

			if auto:
				# Translators: The label of a button to remind the user later about performing some action.
				item = wx.Button(self, label=_("Remind me &later"))
				item.Bind(wx.EVT_BUTTON, self.onLaterButton)
				mainSizer.Add(item)

		# Translators: The label of a button to close a dialog.
		item = wx.Button(self, wx.ID_CLOSE, label=_("&Close"))
		item.Bind(wx.EVT_BUTTON, lambda evt: self.Close())
		mainSizer.Add(item)
		self.Bind(wx.EVT_CLOSE, lambda evt: self.Destroy())
		self.EscapeId = wx.ID_CLOSE

		self.Sizer = mainSizer
		mainSizer.Fit(self)
		self.Show()

	def onDownloadButton(self, evt):
		if config.isInstalledCopy():
			url = self.updateInfo["installerUrl"]
		else:
			url = self.updateInfo["portableUrl"]
		os.startfile(url)
		self.Close()

	def onLaterButton(self, evt):
		state["dontRemindVersion"] = None
		self.Close()

def initialize():
	global autoChecker
	if config.conf["update"]["autoCheck"]:
		autoChecker = AutoUpdateChecker()

def terminate():
	global autoChecker
	autoChecker = None
