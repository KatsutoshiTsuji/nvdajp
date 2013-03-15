#synthDrivers/sapi5.py
#A part of NonVisual Desktop Access (NVDA)
#Copyright (C) 2006-2011 NVDA Contributors <http://www.nvda-project.org/>
#This file is covered by the GNU General Public License.
#See the file COPYING for more details.

import locale
from collections import OrderedDict
import time
import os
import comtypes.client
from comtypes import COMError
import _winreg
import globalVars
import speech
from synthDriverHandler import SynthDriver,VoiceInfo
import config
import nvwave
from logHandler import log

class constants:
	SVSFlagsAsync = 1
	SVSFPurgeBeforeSpeak = 2
	SVSFIsXML = 8

class SynthDriver(SynthDriver):
	supportedSettings=(SynthDriver.VoiceSetting(),SynthDriver.RateSetting(),SynthDriver.PitchSetting(),SynthDriver.VolumeSetting())

	COM_CLASS = "SAPI.SPVoice"

	name="sapi5"
	description="Microsoft Speech API version 5"

	@classmethod
	def check(cls):
		try:
			r=_winreg.OpenKey(_winreg.HKEY_CLASSES_ROOT,cls.COM_CLASS)
			r.Close()
			return True
		except:
			return False

	def __init__(self,_defaultVoiceToken=None):
		"""
		@param _defaultVoiceToken: an optional sapi voice token which should be used as the default voice (only useful for subclasses)
		@type _defaultVoiceToken: ISpeechObjectToken
		"""
		self._pitch=50
		self._initTts(_defaultVoiceToken)

	def terminate(self):
		del self.tts

	def _getAvailableVoices(self):
		voices=OrderedDict()
		v=self._getVoiceTokens()
		# #2629: Iterating uses IEnumVARIANT and GetBestInterface doesn't work on tokens returned by some token enumerators.
		# Therefore, fetch the items by index, as that method explicitly returns the correct interface.
		for i in xrange(len(v)):
			try:
				ID=v[i].Id
				name=v[i].GetDescription()
				try:
					language=locale.windows_locale[int(v[i].getattribute('language').split(';')[0],16)]
				except KeyError:
					language=None
			except COMError:
				log.warning("Could not get the voice info. Skipping...")
			voices[ID]=VoiceInfo(ID,name,language)
		return voices

	def _getVoiceTokens(self):
		"""Provides a collection of sapi5 voice tokens. Can be overridden by subclasses if tokens should be looked for in some other registry location."""
		return self.tts.getVoices()

	def _get_rate(self):
		return (self.tts.rate*5)+50

	def _get_pitch(self):
		return self._pitch

	def _get_volume(self):
		return self.tts.volume

	def _get_voice(self):
		return self.tts.voice.Id
 
	def _get_lastIndex(self):
		bookmark=self.tts.status.LastBookmark
		if bookmark!="" and bookmark is not None:
			return int(bookmark)
		else:
			return None

	def _set_rate(self,rate):
		self.tts.Rate = (rate-50)/5

	def _set_pitch(self,value):
		#pitch is really controled with xml around speak commands
		self._pitch=value

	def _set_volume(self,value):
		self.tts.Volume = value

	def _initTts(self, voice=None):
		self.tts=comtypes.client.CreateObject(self.COM_CLASS)
		if voice:
			# #749: It seems that SAPI 5 doesn't reset the audio parameters when the voice is changed,
			# but only when the audio output is changed.
			# Therefore, set the voice before setting the audio output.
			# Otherwise, we will get poor speech quality in some cases.
			self.tts.voice = voice
		outputDeviceID=nvwave.outputDeviceNameToID(config.conf["speech"]["outputDevice"], True)
		if outputDeviceID>=0:
			self.tts.audioOutput=self.tts.getAudioOutputs()[outputDeviceID]

	def _set_voice(self,value):
		tokens = self._getVoiceTokens()
		# #2629: Iterating uses IEnumVARIANT and GetBestInterface doesn't work on tokens returned by some token enumerators.
		# Therefore, fetch the items by index, as that method explicitly returns the correct interface.
		for i in xrange(len(tokens)):
			voice=tokens[i]
			if value==voice.Id:
				break
		else:
			# Voice not found.
			return
		self._initTts(voice=voice)

	def speak(self,speechSequence):
		textList=[]
		for item in speechSequence:
			if isinstance(item,basestring):
				textList.append(item.replace("<","&lt;"))
			elif isinstance(item,speech.IndexCommand):
				textList.append("<Bookmark Mark=\"%d\" />"%item.index)
			elif isinstance(item,speech.CharacterModeCommand):
				textList.append("<spell>" if item.state else "</spell>")
			elif isinstance(item,speech.SpeechCommand):
				log.debugWarning("Unsupported speech command: %s"%item)
			else:
				log.error("Unknown speech: %s"%item)
		text="".join(textList)
		#Pitch must always be hardcoded
		pitch=(self._pitch/2)-25
		text="<pitch absmiddle=\"%s\">%s</pitch>"%(pitch,text)
		flags=constants.SVSFIsXML|constants.SVSFlagsAsync
		self.tts.Speak(text,flags)

	def cancel(self):
		#if self.tts.Status.RunningState == 2:
		self.tts.Speak(None, 1|constants.SVSFPurgeBeforeSpeak)

	def pause(self,switch):
		if switch:
			self.cancel()
