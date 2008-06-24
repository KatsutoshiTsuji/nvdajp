#scriptHandler.py
#A part of NonVisual Desktop Access (NVDA)
#Copyright (C) 2006-2007 NVDA Contributors <http://www.nvda-project.org/>
#This file is covered by the GNU General Public License.
#See the file COPYING for more details.

import time
import weakref
import inspect
import appModuleHandler
import api
import queueHandler

_numScriptsQueued=0 #Number of scripts that are queued to be executed
_lastScriptTime=0 #Time in MS of when the last script was executed
_lastScriptRef=None #Holds a weakref to the last script that was executed
_lastScriptCount=0 #The amount of times the last script was repeated

def findScript(keyPress):
		return findScript_appModuleLevel(keyPress)

def findScript_appModuleLevel(keyPress):
	focusObject=api.getFocusObject()
	if not focusObject:
		return None
	appModule=focusObject.appModule
	func=appModule.getScript(keyPress) if appModule else None
	if func:
		return func
	return findScript_defaultAppModuleLevel(keyPress)

def findScript_defaultAppModuleLevel(keyPress):
	default=appModuleHandler.default
	func=default.getScript(keyPress)
	if func:
		return func
	return findScript_virtualBufferLevel(keyPress)

def findScript_virtualBufferLevel(keyPress):
	virtualBuffer=api.getFocusObject().virtualBuffer
	if virtualBuffer and not virtualBuffer.passThrough:
		func=virtualBuffer.getScript(keyPress)
		if func:
			return func
	return findScript_NVDAObjectLevel(keyPress)

def findScript_NVDAObjectLevel(keyPress):
	objList=list(reversed(api.getFocusAncestors()))
	objList.insert(0,api.getFocusObject())
	for obj in objList:
		func=obj.getScript(keyPress)
		if func:
			return func
	return None

def getScriptName(script):
	return script.__name__[7:]

def getScriptLocation(script):
	return script.__module__

def getScriptDescription(script):
	return script.__doc__

def _queueScriptCallback(script,keyPress):
	global _numScriptsQueued
	_numScriptsQueued-=1
	executeScript(script,keyPress)

def queueScript(script,keyPress):
	global _numScriptsQueued
	_numScriptsQueued+=1
	queueHandler.queueFunction(queueHandler.eventQueue,_queueScriptCallback,script,keyPress)

def executeScript(script,keyPress):
	"""Executes a given script (function) passing it the given keyPress.
	It also keeps track of the execution of duplicate scripts with in a certain amount of time, and counts how many times this happens.
	Use L{getLastScriptRepeateCount} to find out this count value.
	@param script: the function or method that should be executed. The function or method must take an argument of 'keyPress'.
	@type script: callable.
	@param keyPress: the key press that activated this script
	@type keyPress: an NVDA keyPress
	"""
	global _lastScriptTime, _lastScriptCount, _lastScriptRef 
	scriptTime=time.time()
	scriptRef=weakref.ref(script)
	if (scriptTime-_lastScriptTime)<=0.5 and _lastScriptRef and script==_lastScriptRef():
		_lastScriptCount+=1
	else:
		_lastScriptCount=0
	_lastScriptRef=scriptRef
	_lastScriptTime=scriptTime
	script(keyPress)

def getLastScriptRepeateCount():
	"""The count of how many times the most recent script has been executed.
	This should only be called from with in a script.
	@returns: a value greater or equal to 0. If the script has not been repeated it is 0, if it has been repeated once its 1, and so forth.
	@rtype: integer
	"""
	if (time.time()-_lastScriptTime)>0.5:
		return 0
	else:
		return _lastScriptCount

def isScriptWaiting():
	return bool(_numScriptsQueued)

def isCurrentScript(scriptFunc):
	"""Finds out if the given script is equal to the script that L{isCurrentScript} is being called from.
	@param scriptFunc: the script retreaved from ScriptableObject.getScript(keyPress)
	@type scriptFunc: Instance method
	@returns: True if they are equal, False otherwise
	@rtype: boolean
	"""
	try:
	 	givenFunc=getattr(scriptFunc.im_self.__class__,scriptFunc.__name__)
	except AttributeError:
		globalVars.log.debug("Could not get unbound method from given script",exc_info=True) 
		return False
	parentFrame=inspect.currentframe().f_back
	try:
		realObj=parentFrame.f_locals['self']
	except KeyError:
		globalVars.log.debug("Could not get self instance from parent frame instance method",exc_info=True)
		return False
	try:
		realFunc=getattr(realObj.__class__,parentFrame.f_code.co_name)
	except AttributeError:
		globalVars.log.debug("Could not get unbound method from parent frame instance",exc_info=True)
		return False
	return givenFunc==realFunc
