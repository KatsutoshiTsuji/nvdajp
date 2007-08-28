#keyboardHandler.py
#A part of NonVisual Desktop Access (NVDA)
#Copyright (C) 2006-2007 NVDA Contributors <http://www.nvda-project.org/>
#This file is covered by the GNU General Public License.
#See the file COPYING for more details.

"""Keyboard support"""

import winUser
import ctypes
import time
import vkCodes
import debug
import speech
from keyUtils import key, keyName, sendKey
import scriptHandler
import globalVars
import queueHandler
import config
import locale

keyUpIgnoreSet=set()
passKeyThroughCount=-1 #If 0 or higher then key downs and key ups will be passed straight through
NVDAModifierKey=None
usedNVDAModifierKey=False
lastNVDAModifierKey=None
lastNVDAModifierKeyTime=None
unPauseByControlUp=False

def passNextKeyThrough():
	global passKeyThroughCount
	if passKeyThroughCount==-1:
		passKeyThroughCount=0

def isNVDAModifierKey(vkCode,extended):
	if config.conf["keyboard"]["useNumpadInsertAsNVDAModifierKey"] and vkCode==winUser.VK_INSERT and not extended:
		return True
	elif config.conf["keyboard"]["useExtendedInsertAsNVDAModifierKey"] and vkCode==winUser.VK_INSERT and extended:
		return True
	elif config.conf["keyboard"]["useCapsLockAsNVDAModifierKey"] and vkCode==winUser.VK_CAPITAL:
		return True
	else:
		return False

def speakToggleKey(vkCode):
	toggleState=bool(not winUser.getKeyState(vkCode)&1)
	if vkCode==winUser.VK_CAPITAL:
			queueHandler.queueFunction(queueHandler.interactiveQueue,speech.speakMessage,_("caps lock %s")%(_("on") if toggleState else _("off")))
	elif vkCode==winUser.VK_NUMLOCK:
			queueHandler.queueFunction(queueHandler.interactiveQueue,speech.speakMessage,_("num lock %s")%(_("on") if toggleState else _("off")))
	elif vkCode==winUser.VK_SCROLL:
			queueHandler.queueFunction(queueHandler.interactiveQueue,speech.speakMessage,_("scroll lock %s")%(_("on") if toggleState else _("off")))

@ctypes.CFUNCTYPE(ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int)
def internal_keyDownEvent(vkCode,scanCode,extended,injected):
	"""Event called by pyHook when it receives a keyDown. It sees if there is a script tied to this key and if so executes it. It also handles the speaking of characters, words and command keys.
"""
	try:
		global NVDAModifierKey, usedNVDAModifierKey, lastNVDAModifierKey, lastNVDAModifierKeyTime, passKeyThroughCount, unPauseByControlUp
		#Injected keys should be ignored
		if injected:
			return True
		if passKeyThroughCount>=0:
			passKeyThroughCount+=1
			return True
		vkName=vkCodes.byCode.get(vkCode,"").lower()
		if not vkName and vkCode>=32 and vkCode<128:
			vkName=unichr(vkCode).lower()
		if vkCode in (winUser.VK_CONTROL,winUser.VK_LCONTROL,winUser.VK_RCONTROL):
			if speech.isPaused:
				unPauseByControlUp=True
			else:
				queueHandler.queueFunction(queueHandler.interactiveQueue,speech.pauseSpeech,True)
		else:
			unPauseByControlUp=False
			globalVars.keyCounter+=1
			queueHandler.queueFunction(queueHandler.interactiveQueue,speech.cancelSpeech)
		if lastNVDAModifierKey and (vkCode,extended)==lastNVDAModifierKey:
			lastNVDAModifierKey=None
			if (time.time()-lastNVDAModifierKeyTime)<0.5:
				speakToggleKey(vkCode)
				return True
		lastNVDAModifierKey=None
		if isNVDAModifierKey(vkCode,extended):
			NVDAModifierKey=(vkCode,extended)
			return False
		if vkCode in [winUser.VK_CONTROL,winUser.VK_LCONTROL,winUser.VK_RCONTROL,winUser.VK_SHIFT,winUser.VK_LSHIFT,winUser.VK_RSHIFT,winUser.VK_MENU,winUser.VK_LMENU,winUser.VK_RMENU,winUser.VK_LWIN,winUser.VK_RWIN]:
			return True
		modifierList=[]
		if NVDAModifierKey:
			modifierList.append("nvda")
		if winUser.getKeyState(winUser.VK_CONTROL)&32768:
			modifierList.append("control")
		if winUser.getKeyState(winUser.VK_SHIFT)&32768:
			modifierList.append("shift")
		if winUser.getKeyState(winUser.VK_MENU)&32768:
			modifierList.append("alt")
		if winUser.getKeyState(winUser.VK_LWIN)&32768:
			modifierList.append("win")
		if winUser.getKeyState(winUser.VK_RWIN)&32768:
			modifierList.append("win")
		if len(modifierList) > 0:
			modifiers=frozenset(modifierList)
		else:
			modifiers=None
		mainKey=vkName
		if extended==1:
			mainKey="extended%s"%mainKey
		keyPress=(modifiers,mainKey)
		debug.writeMessage("key press: %s"%keyName(keyPress))
		if globalVars.keyboardHelp or (config.conf["keyboard"]["speakCommandKeys"] and not ( not keyPress[0] and config.conf["keyboard"]["speakTypedCharacters"])):
			labelList=[]
			if keyPress[0] is not None:
				labelList.extend(keyPress[0])
			ch=ctypes.windll.user32.MapVirtualKeyW(vkCode,winUser.MAPVK_VK_TO_CHAR)
			if ch>32:
				labelList.append(unichr(ch))
			else:
				labelList.append(keyPress[1])
			queueHandler.queueFunction(queueHandler.interactiveQueue,speech.speakMessage,"+".join(labelList))
		script=scriptHandler.findScript(keyPress)
		if script:
			scriptName=scriptHandler.getScriptName(script)
			scriptLocation=scriptHandler.getScriptLocation(script)
			scriptDescription=scriptHandler.getScriptDescription(script)
			if globalVars.keyboardHelp and scriptName!="keyboardHelp":
				queueHandler.queueFunction(queueHandler.interactiveQueue,speech.speakMessage,"%s"%scriptName.replace('_',' '))
				queueHandler.queueFunction(queueHandler.interactiveQueue,speech.speakMessage,_("Description: %s")%scriptDescription)
				queueHandler.queueFunction(queueHandler.interactiveQueue,speech.speakMessage,_("Location: %s")%scriptLocation)
			else:
				queueHandler.queueFunction(queueHandler.interactiveQueue,script,keyPress)
		if script or globalVars.keyboardHelp:
			keyUpIgnoreSet.add((vkCode,extended))
			if NVDAModifierKey:
				usedNVDAModifierKey=True 
			return False
		else:
			speakToggleKey(vkCode)
			return True
	except:
		debug.writeException("keyboardHandler.internal_keyDownEvent")
		speech.speakMessage("Error in keyboardHandler.internal_keyDownEvent",wait=True)
		return True
@ctypes.CFUNCTYPE(ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int)
def internal_keyUpEvent(vkCode,scanCode,extended,injected):
	"""Event that pyHook calls when it receives keyUps"""
	try:
		global NVDAModifierKey, usedNVDAModifierKey, lastNVDAModifierKey, lastNVDAModifierKeyTime, passKeyThroughCount, unPauseByControlUp
		if injected:
			return True
		elif passKeyThroughCount>=1:
			passKeyThroughCount-=1
			if passKeyThroughCount==0:
				passKeyThroughCount=-1
			return True
		if unPauseByControlUp and vkCode in (winUser.VK_CONTROL,winUser.VK_LCONTROL,winUser.VK_RCONTROL):
			queueHandler.queueFunction(queueHandler.interactiveQueue,speech.pauseSpeech,False)
			unPauseByControlUp=False
		if NVDAModifierKey and (vkCode,extended)==NVDAModifierKey:
			if not usedNVDAModifierKey:
				lastNVDAModifierKey=NVDAModifierKey
				lastNVDAModifierKeyTime=time.time()
			NVDAModifierKey=None
			usedNVDAModifierKey=False
			return False
		elif (vkCode,extended) in keyUpIgnoreSet:
			keyUpIgnoreSet.remove((vkCode,extended))
			return False
		elif vkCode in [winUser.VK_CONTROL,winUser.VK_LCONTROL,winUser.VK_RCONTROL,winUser.VK_SHIFT,winUser.VK_LSHIFT,winUser.VK_RSHIFT,winUser.VK_MENU,winUser.VK_LMENU,winUser.VK_RMENU,winUser.VK_LWIN,winUser.VK_RWIN]:
			return True
		else:
			return True
	except:
		debug.writeException("keyboardHandler.internal_keyUpEvent")
		speech.speakMessage("Error in keyboardHandler.internal_keyUpEvent",wait=True)
		return True

@ctypes.CFUNCTYPE(ctypes.c_voidp,ctypes.c_wchar)
def internal_typeCharacterEvent(ch):
	if ord(ch)>=32:
		queueHandler.queueFunction(queueHandler.eventQueue,speech.speakTypedCharacters,ch)

#Register internal key press event with  operating system

def initialize():
	"""Initialises keyboard support."""
	ctypes.cdll.keyHook.initialize(internal_keyDownEvent,internal_keyUpEvent)
	ctypes.cdll.charHook.initialize(internal_typeCharacterEvent)

def terminate():
	ctypes.cdll.keyHook.terminate()
	ctypes.cdll.charHook.terminate()
