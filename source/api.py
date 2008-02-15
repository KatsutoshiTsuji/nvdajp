#api.py
#A part of NonVisual Desktop Access (NVDA)
#Copyright (C) 2006-2007 NVDA Contributors <http://www.nvda-project.org/>
#This file is covered by the GNU General Public License.
#See the file COPYING for more details.

"""General functions for NVDA"""

import pythoncom
import weakref
import logging
import textHandler
import globalVars
import speech
import virtualBufferHandler
import NVDAObjects
import winUser
import wx
import core
import queueHandler
import controlTypes
import win32clipboard
import win32con

#User functions

def quit():
	"""
Instructs the GUI that you want to quit. The GUI responds by bringing up a dialog asking you if you want to exit.
"""
	gui.quit()

def findObjectWithFocus():
	"""Walks the object hyerarchy starting at the desktop Window (root object) and follows the activeChild property of each object until it can not go any further - this will be the object with focus.
@returns: object with focus
@rtype: L{NVDAObjects.NVDAObject}
"""
	prevObj=getDesktopObject()
	obj=prevObj.activeChild
	while obj and obj!=prevObj:
		prevObj=obj
		obj=obj.activeChild
	if isinstance(prevObj,NVDAObjects.NVDAObject) and prevObj.hasFocus:
		return prevObj
	else:
		return None

def getFocusObject():
	"""
Gets the current object with focus.
@returns: the object with focus
@rtype: L{NVDAObjects.NVDAObject}
"""
	return globalVars.focusObject

def getForegroundObject():
	"""Gets the current foreground object.
@returns: the current foreground object
@rtype: L{NVDAObjects.NVDAObject}
"""
	return globalVars.foregroundObject

def setForegroundObject(obj):
	"""Stores the given object as the current foreground object. (Note: it does not physically change the operating system foreground window, but only allows NVDA to keep track of what it is).
@param obj: the object that will be stored as the current foreground object
@type obj: NVDAObjects.NVDAObject
"""
	if not isinstance(obj,NVDAObjects.NVDAObject):
		return False
	globalVars.foregroundObject=obj
	if globalVars.log.getEffectiveLevel()<=logging.INFO:
		globalVars.log.info("%s %s %s %s"%(obj.name or "",controlTypes.speechRoleLabels[obj.role],obj.value or "",obj.description or ""))
	return True

def setFocusObject(obj,ancestors=None):
	"""Stores an object as the current focus object. (Note: this does not physically change the window with focus in the operating system, but allows NVDA to keep track of the correct object).
Before overriding the last object, this function calls event_looseFocus on the object to notify it that it is loosing focus. 
@param obj: the object that will be stored as the focus object
@type obj: NVDAObjects.NVDAObject
"""
	if not isinstance(obj,NVDAObjects.NVDAObject):
		return False
	if globalVars.focusObject and hasattr(globalVars.focusObject,"event_looseFocus"):
		try:
			globalVars.focusObject.event_looseFocus()
		except:
			globalVars.log.error("event_looseFocus in focusObject", exc_info=True)
	oldAncestors=globalVars.focusAncestors
	if not ancestors:
		ancestors=[]
		parent=obj.parent
		while parent:
			ancestors.insert(0,parent)
			parent=parent.parent
	commonLevel=None
	oldAncestors=globalVars.focusAncestors
	oldAncestors.append(globalVars.focusObject)
	for index in range(min(len(oldAncestors),len(ancestors))):
		if oldAncestors[index]==ancestors[index]:
			commonLevel=index
		else:
			break
	if commonLevel is None and len(ancestors)>0 and ancestors[0]==globalVars.foregroundObject:
		commonLevel=0
	if commonLevel is None:
		globalVars.focusDifferenceLevel=0
	else:
		globalVars.focusDifferenceLevel=commonLevel+1
	globalVars.focusObject=obj
	globalVars.focusAncestors=ancestors
	if not obj.virtualBuffer or not obj.virtualBuffer.isAlive():
		virtualBufferObject=None
		for o in globalVars.focusAncestors[globalVars.focusDifferenceLevel:]+[globalVars.focusObject]:
			virtualBufferObject=virtualBufferHandler.update(o)
			if virtualBufferObject:
				obj.virtualBuffer=virtualBufferObject
				break
	if globalVars.log.getEffectiveLevel()<=logging.INFO:
		globalVars.log.info("%s %s %s %s"%(obj.name or "",controlTypes.speechRoleLabels[obj.role],obj.value or "",obj.description or ""))
	return True

def getFocusDifferenceLevel():
	return globalVars.focusDifferenceLevel

def getFocusAncestors():
	return globalVars.focusAncestors

def getMouseObject():
	"""Returns the object that is directly under the mouse"""
	return globalVars.mouseObject

def setMouseObject(obj):
	"""Tells NVDA to remember the given object as the object that is directly under the mouse"""
	if globalVars.log.getEffectiveLevel()<=logging.INFO:
		globalVars.log.info("%s %s %s %s"%(obj.name or "",controlTypes.speechRoleLabels[obj.role],obj.value or "",obj.description or ""))
	globalVars.mouseObject=obj

def getDesktopObject():
	"""Get the desktop object"""
	return globalVars.desktopObject

def setDesktopObject(obj):
	"""Tells NVDA to remember the given object as the desktop object"""
	if globalVars.log.getEffectiveLevel()<=logging.INFO:
		globalVars.log.info("%s %s %s %s"%(obj.name or "",controlTypes.speechRoleLabels[obj.role],obj.value or "",obj.description or ""))
	globalVars.desktopObject=obj

def getNavigatorObject():
	"""Gets the current navigator object. Navigator objects can be used to navigate around the operating system (with the number pad) with out moving the focus. 
@returns: the current navigator object
@rtype: L{NVDAObjects.NVDAObject}
"""
	return globalVars.navigatorObject

def setNavigatorObject(obj):
	"""Sets an object to be the current navigator object. Navigator objects can be used to navigate around the operating system (with the number pad) with out moving the focus.  
@param obj: the object that will be set as the current navigator object
@type obj: NVDAObjects.NVDAObject  
"""
	if not isinstance(obj,NVDAObjects.NVDAObject):
		return False
	if globalVars.log.getEffectiveLevel()<=logging.INFO:
		globalVars.log.info("%s %s %s %s"%(obj.name or "",controlTypes.speechRoleLabels[obj.role],obj.value or "",obj.description or ""))
	globalVars.navigatorObject=obj
	globalVars.reviewPosition=obj.makeTextInfo(textHandler.POSITION_CARET)

def isTypingProtected():
	"""Checks to see if key echo should be suppressed because the focus is currently on an object that has its protected state set.
@returns: True if it should be suppressed, False otherwise.
@rtype: boolean
"""
	focusObject=getFocusObject()
	if focusObject and (controlTypes.STATE_PROTECTED in focusObject.states or focusObject.role==controlTypes.ROLE_PASSWORDEDIT):
		return True
	else:
		return False

def toggleVirtualBufferPassThrough():
	"""Toggles virtualBufferPassThroughMode on or off. This mode is so that virtualBuffers can either capture, or ignore, key presses.
This function also speaks the state of the mode as it changes.
"""
	if globalVars.virtualBufferPassThrough:
		speech.speakMessage(_("virtual buffer pass through")+" "+_("off"))
		globalVars.virtualBufferPassThrough=False
	else:
		speech.speakMessage(_("virtual buffer pass through")+" "+_("on"))
		globalVars.virtualBufferPassThrough=True

def isVirtualBufferPassThrough():
	"""Gets the current state of the virtualBuffer pass through mode. This mode is so that virtualBuffers can either capture, or ignore, key presses.
@returns: true if on or false if off.
@rtype: boolean
 """
	return globalVars.virtualBufferPassThrough

def createStateList(states):
	"""Breaks down the given integer in to a list of numbers that are 2 to the power of their position.""" 
	return [x for x in [1<<y for y in xrange(32)] if x&states]


def moveMouseToNVDAObject(obj):
	"""Moves the mouse to the given NVDA object's position""" 
	location=obj.location
	if location and (len(location)==4):
		(left,top,width,height)=location
		x=(left+left+width)/2
		y=(top+top+height)/2
		winUser.setCursorPos(x,y)

def processPendingEvents():
	wx.Yield()
	pythoncom.PumpWaitingMessages()
	queueHandler.flushQueue(queueHandler.eventQueue)

def copyToClip(text):
	"""Copies the given text to the windows clipboard.
@returns: True if it succeeds, False otherwise.
@rtype: boolean
@param text: the text which will be copied to the clipboard
@type obj: string
"""
	if isinstance(text,basestring) and len(text)>0 and not text.isspace():
		win32clipboard.OpenClipboard()
		try:
			win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, text)
		finally:
			win32clipboard.CloseClipboard()
		win32clipboard.OpenClipboard() # there seems to be a bug so to retrieve unicode text we have to reopen the clipboard
		try:
			got = 	win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
		finally:
			win32clipboard.CloseClipboard()
		if got == text:
			return True
	return False
