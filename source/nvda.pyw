#nvda.pyw
#A part of NonVisual Desktop Access (NVDA)
#Copyright (C) 2006-2007 Michael Curran <mick@kulgan.net>
#This file is covered by the GNU General Public License.
#See the file COPYING for more details.

import logging
import os
import sys
import codecs
import tempfile
import ctypes
import winsound
import locale
import gettext
import time
import optparse
import win32gui
import win32con
import globalVars
import logObj
import winUser
import winKernel

restartByErrorCount=0

class NoConsoleOptionParser(optparse.OptionParser):

	def print_help(self, file=None):
		win32gui.MessageBox(0, self.format_help(), "Help", 0)

	def error(self, msg):
		out = ""
		if self.usage:
			out = self.get_usage()
		out += "\nerror: %s" % msg
		win32gui.MessageBox(0, out, "Error", 0)
		sys.exit(2)

def abortWithError(code):
	globalVars.log.critical("core stop not due to exit/restart",exc_info=True)
	winsound.PlaySound("SystemHand",winsound.SND_ALIAS)
	winsound.PlaySound("waves\\exit.wav",winsound.SND_FILENAME)
	winUser.setSystemScreenReaderFlag(False)
	sys.exit(code)


globalVars.startTime=time.time()

if getattr(sys, "frozen", None):
	# We are running as an executable.
	# Append the path of the executable to sys so we can import modules from the dist dir.
	sys.path.append(sys.prefix)
	os.chdir(sys.prefix)
	logFileName='%s\\nvda.log'%tempfile.gettempdir()
	stderrFileName='%s\\nvda_stderr.log'%tempfile.gettempdir()
else:
	os.chdir(sys.path[0])
	logFileName='nvda.log'
	stderrFileName='stderr.log'

#Localization settings
locale.setlocale(locale.LC_ALL,'')
try:
	gettext.translation('nvda',localedir='locale',languages=[locale.getlocale()[0]]).install(True)
except:
	gettext.install('nvda',unicode=True)

#Process option arguments
parser=NoConsoleOptionParser()
parser.add_option('-q','--quit',action="store_true",dest='quit',default=False,help="Quit already running copy of NVDA")
parser.add_option('-r','--replace',action="store_true",dest='replace',default=False,help="Quit already running copy of NVDA and start this one")
parser.add_option('-f','--log-file',dest='logFileName',default=logFileName,help="The file where log messages should be written to")
parser.add_option('-l','--log-level',type="int",dest='logLevel',default=0,help="The lowest level of message logged (debug 10, info 20, warning 30, error 40, critical 50), default is warning") 
parser.add_option('-c','--config-file',dest='configFileName',default="./nvda.ini",help="The file where all settings are stored")
parser.add_option('-m','--minimal',action="store_true",dest='minimal',default=False,help="No sounds, no interface, no start message etc")
(globalVars.appArgs,extraArgs)=parser.parse_args()

#Handle running multiple instances of NVDA
try:
	oldAppWindowHandle=win32gui.FindWindow('wxWindowClassNR','NVDA')
except:
	oldAppWindowHandle=0
if oldAppWindowHandle and win32gui.IsWindow(oldAppWindowHandle): 
	processID,threadID=winUser.getWindowThreadProcessID(oldAppWindowHandle)
	if globalVars.appArgs.quit or globalVars.appArgs.replace:
		win32gui.PostMessage(oldAppWindowHandle,win32con.WM_QUIT,0,0)
		timeout=0
		ok=False
		while not ok and timeout<3000:
			win32gui.PumpWaitingMessages()
			time.sleep(0.001)
			if not (oldAppWindowHandle and win32gui.IsWindow(oldAppWindowHandle)): 
				h=winKernel.openProcess(winKernel.PROCESS_VM_READ,False,processID)
				if h<=0:
					ok=True
				else:
					winKernel.closeHandle(h)
			timeout+=1
		try:
			oldAppWindowHandle=win32gui.FindWindow('wxWindowClassNR','NVDA')
		except:
			oldAppWindowHandle=0
		if oldAppWindowHandle and win32gui.IsWindow(oldAppWindowHandle):
			win32gui.MessageBox(0, "Error quitting NVDA", "Error", 0)
			sys.exit(1)
if globalVars.appArgs.quit or oldAppWindowHandle:
	sys.exit(0)

#os.environ['PYCHECKER']="--limit 10000 -q --changetypes"
#import pychecker.checker
#Initial logging and logging code

stderrFile=codecs.open(stderrFileName,"w","utf-8","ignore")
if stderrFile is None:
	sys.exit()
sys.stderr=stderrFile
sys.stdout=stderrFile


logLevel=globalVars.appArgs.logLevel
if logLevel<=0:
	logLevel=logging.WARN
log=logObj.Logger("NVDA",logLevel)
logHandler=logObj.FileHandler(globalVars.appArgs.logFileName,"w")
logFormatter=logging.Formatter("%(levelname)s - %(codepath)s:\n%(message)s")
logHandler.setFormatter(logFormatter)
log.addHandler(logHandler)
globalVars.log=log
if not globalVars.appArgs.minimal:
	winsound.PlaySound("waves\\start.wav",winsound.SND_FILENAME|winsound.SND_ASYNC)
winUser.setSystemScreenReaderFlag(True)
try:
	import core
except:
	abortWithError(3)
res=core.main()
if res in [core.CORE_MAINLOOPERROR,core.CORE_RESTART]:
	winsound.PlaySound("waves\\exit.wav",winsound.SND_FILENAME)
	os.spawnv(os.P_NOWAIT,sys.executable,[os.path.basename(sys.executable)]+sys.argv)
	os._exit(0)
elif res==core.CORE_INITERROR:
	abortWithError(4)
winUser.setSystemScreenReaderFlag(False)
if not globalVars.appArgs.minimal:
	winsound.PlaySound("waves\\exit.wav",winsound.SND_FILENAME)
globalVars.log.info("NVDA exit")
del globalVars.log
