#audio.py
#A part of NonVisual Desktop Access (NVDA)
#Copyright (C) 2006-2007 Michael Curran <mick@kulgan.net>
#This file is covered by the GNU General Public License.
#See the file COPYING for more details.

"""High-level functions to speak information.
@var speechMode: allows speech if true
@type speechMode: boolean
""" 

import time
from textProcessing import *
import debug
import config
import tones
import synthDriverHandler

speechMode_off=0
speechMode_beeps=1
speechMode_talk=2
speechMode=2
speechMode_beeps_ms=15
beenCanceled=True

def initialize():
	"""Loads and sets the synth driver configured in nvda.ini."""
	synthDriverHandler.setDriver(config.conf["speech"]["synth"])

def getLastIndex():
	"""Gets the last index passed by the synthesizer. Indexing is used so that its possible to find out when a certain peace of text has been spoken yet. Usually the character position of the text is passed to speak functions as the index.
@returns: the last index encountered
@rtype: int
"""
	return synthDriverHandler.getLastIndex()

def processText(text):
	"""Processes the text using the L{textProcessing} module which converts punctuation so it is suitable to be spoken by the synthesizer. This function makes sure that all punctuation is included if it is configured so in nvda.ini.
@param text: the text to be processed
@type text: string
"""
	text=processTextSymbols(text,expandPunctuation=config.conf["speech"]["speakPunctuation"])
	return text

def cancel():
	"""Interupts the synthesizer from currently speaking"""
	global beenCanceled
	if beenCanceled:
		return
	elif speechMode==speechMode_off:
		return
	elif speechMode==speechMode_beeps:
		return
	synthDriverHandler.cancel()
	beenCanceled=True

def speakMessage(text,wait=False,index=None):
	"""Speaks a given message.
This function will not speak if L{speechMode} is false.
@param text: the message to speak
@type text: string
@param wait: if true, the function will not return until the text has finished being spoken. If false, the function will return straight away.
@type wait: boolean
@param index: the index to mark this current text with 
@type index: int
"""
	global beenCanceled
	if speechMode==speechMode_off:
		return
	elif speechMode==speechMode_beeps:
		tones.beep(config.conf["speech"]["beepSpeechModePitch"],speechMode_beeps_ms)
		return
	beenCanceled=False
	text=processText(text)
	if text and not text.isspace():
		synthDriverHandler.speakText("\n"+text+"\n",wait=wait,index=index)

def speakObjectProperties(name=None,typeString=None,stateText=None,value=None,description=None,keyboardShortcut=None,position=None,level=None,contains=None,wait=False,index=None):
	"""Speaks some given object properties.
This function will not speak if L{speechMode} is false.
@param name: object name
@type name: string
@param typeString: object type string
@type typeString: string
@param stateText: object state text
@type stateText: string
@param value: object value
@type value: string
@param description: object description
@type description: string
@param keyboardShortcut: object keyboard shortcut
@type keyboardShortcut: string
@param position: object position info
@type position: string
@param wait: if true, the function will not return until the text has finished being spoken. If false, the function will return straight away.
@type wait: boolean
@param index: the index to mark this current text with 
@type index: int
"""
	global beenCanceled
	if speechMode==speechMode_off:
		return
	elif speechMode==speechMode_beeps:
		tones.beep(config.conf["speech"]["beepSpeechModePitch"],speechMode_beeps_ms)
		return
	beenCanceled=False
	if description and name==description:
		description=None
	text=""
	if config.conf["presentation"]["sayStateFirst"] and (stateText is not None):
		multiList=[stateText,name,typeString,value,description,level,contains,position]
	else:
		multiList=[name,typeString,value,stateText,description,level,contains,position]
	if config.conf["presentation"]["reportKeyboardShortcuts"]:
		multiList.append(keyboardShortcut)
	for multi in filter(lambda x: isinstance(x,basestring) and (len(x)>0) and not x.isspace(),multiList):
		text="%s %s"%(text,multi)
	if text and not text.isspace():
		text=processText(text)
		synthDriverHandler.speakText(text,wait=wait,index=index)

def speakSymbol(symbol,wait=False,index=None):
	"""Speaks a given single character.
This function will not speak if L{speechMode} is false.
If the character is uppercase, then the pitch of the synthesizer will be altered by a value in nvda.ini and then set back to its origional value. This is to audibly denote capital letters.
Before passing the symbol to the synthersizer, L{textProcessing.processSymbol} is used to expand the symbol to a  speakable word.
@param symbol: the symbol to speak
@type symbol: string
@param wait: if true, the function will not return until the text has finished being spoken. If false, the function will return straight away.
@type wait: boolean
@param index: the index to mark this current text with 
@type index: int
"""
	global beenCanceled
	if speechMode==speechMode_off:
		return
	elif speechMode==speechMode_beeps:
		tones.beep(config.conf["speech"]["beepSpeechModePitch"],speechMode_beeps_ms)
		return
	beenCanceled=False
	text=processSymbol(symbol)
	if symbol is not None and len(symbol)==1 and symbol.isupper(): 
		uppercase=True
	else:
		uppercase=False
	if uppercase:
		if config.conf["speech"][synthDriverHandler.driverName]["sayCapForCapitals"]:
			text=_("cap %s")%text
		oldPitch=config.conf["speech"][synthDriverHandler.driverName]["pitch"]
		synthDriverHandler.driverObject.pitch=99
	synthDriverHandler.speakText(text,wait=wait,index=index)
	if uppercase:
		synthDriverHandler.driverObject.pitch=oldPitch

def speakText(text,wait=False,index=None):
	"""Speaks some given text.
This function will not speak if L{speechMode} is false.
@param text: the message to speak
@type text: string
@param wait: if true, the function will not return until the text has finished being spoken. If false, the function will return straight away.
@type wait: boolean
@param index: the index to mark this current text with, its best to use the character position of the text if you know it 
@type index: int
"""
	global beenCanceled
	if speechMode==speechMode_off:
		return
	elif speechMode==speechMode_beeps:
		tones.beep(config.conf["speech"]["beepSpeechModePitch"],speechMode_beeps_ms)
		return
	beenCanceled=False
	text=processText(text)
	if text and not text.isspace():
		synthDriverHandler.speakText(text,wait=wait,index=index)
