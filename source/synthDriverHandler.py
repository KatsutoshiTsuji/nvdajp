#synthDrivers/__init__.py
#A part of NonVisual Desktop Access (NVDA)
#Copyright (C) 2006-2007 NVDA Contributors <http://www.nvda-project.org/>
#This file is covered by the GNU General Public License.
#See the file COPYING for more details.

import os
import debug
import config
import queueHandler
import speech

#This is here so that the synthDrivers are able to import modules from the synthDrivers dir themselves
__path__=['.\\synthDrivers']

_curSynth=None

def getSynthList():
	synthList=[]
	for name in [os.path.splitext(x)[0] for x in os.listdir(__path__[0]) if (x.endswith('.py') and not x.startswith('_'))]:
		try:
			synth=__import__(name,globals(),locals(),[]).SynthDriver()
			if synth.check():
				synthList.append((synth.name,synth.description))
		except:
			pass
	return synthList

def getSynth():
	return _curSynth

def setSynth(name):
	global _curSynth
	if name is None: 
		_curSynth.terminate()
		_curSynth=None
		return True
	if name=='auto':
		name='espeak'
	try:
		newSynth=__import__(name,globals(),None,[]).SynthDriver()
		if _curSynth and _curSynth.name == newSynth.name:
			_curSynth.cancel()
			_curSynth.terminate()
			_curSynth = None
		newSynth.initialize()
		updatedConfig=config.updateSynthConfig(name)
		if not updatedConfig:
			if newSynth.hasVoice:
				newSynth.voice=config.conf["speech"][name]["voice"]
			if newSynth.hasVariant:
				newSynth.variant=config.conf["speech"][name]["variant"]
			if newSynth.hasRate:
				newSynth.rate=config.conf["speech"][name]["rate"]
			if newSynth.hasPitch:
				newSynth.pitch=config.conf["speech"][name]["pitch"]
			if newSynth.hasVolume:
				newSynth.volume=config.conf["speech"][name]["volume"]
		else:
			if newSynth.hasVoice:
				config.conf["speech"][name]["voice"]=newSynth.voice
			if newSynth.hasVariant:
				config.conf["speech"][name]["variant"]=newSynth.variant
			if newSynth.hasRate:
				config.conf["speech"][name]["rate"]=newSynth.rate
			if newSynth.hasPitch:
				config.conf["speech"][name]["pitch"]=newSynth.pitch
			if newSynth.hasVolume:
				config.conf["speech"][name]["volume"]=newSynth.volume
		if _curSynth:
			_curSynth.cancel()
			_curSynth.terminate()
		_curSynth=newSynth
		config.conf["speech"]["synth"]=name
		debug.writeMessage("Loaded synthDriver %s"%name)
		return True
	except:
		debug.writeException("setSynth")
		if not _curSynth and name not in ['espeak','silence']:
			setSynth('espeak')
		elif not _curSynth and name=='espeak':
			setSynth('silence')
		return False
