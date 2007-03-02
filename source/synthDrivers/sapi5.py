#synthDrivers/sapi5.py
#A part of NonVisual Desktop Access (NVDA)
#Copyright (C) 2006-2007 Michael Curran <mick@kulgan.net>
#This file is covered by the GNU General Public License.
#See the file COPYING for more details.

import time
import os
import comtypesClient
import _winreg
import baseObject
import debug
import globalVars

name="sapi5"
description="Microsoft Speech API version 5 (sapi.SPVoice)"

def check():
	try:
		r=_winreg.OpenKey(_winreg.HKEY_CLASSES_ROOT,"SAPI.SPVoice")
		r.Close()
		return True
	except:
		return False

class constants:
	SVSFlagsAsync = 1
	SVSFPurgeBeforeSpeak = 2
	SVSFIsXML = 8

class synthDriver(baseObject.autoPropertyObject):

	def __init__(self):
		self.tts = comtypesClient.CreateObject('sapi.SPVoice')
		self._rate=(self.tts.rate*5)+50
		self._voice=1
		self._pitch=50
		self._volume=self.tts.volume
		self.voiceNames=[]
		try:
			for num in range(self.tts.GetVoices().Count):
				self.voiceNames.append(self.tts.GetVoices()[num].GetDescription())
		except:
			pass

	def _get_rate(self):
		return self._rate

	def _get_pitch(self):
		return self._pitch

	def _get_volume(self):
		return self._volume

	def _get_voice(self):
		return self._voice

	def _get_lastIndex(self):
		bookmark=self.tts.status.LastBookmark
		if bookmark!="" and bookmark is not None:
			return int(bookmark)
		else:
			return -1

	def _set_rate(self,rate):
		self.tts.Rate = (rate-50)/5
		self._rate=rate

	def _set_pitch(self,value):
		#pitch is really controled with xml around speak commands
		self._pitch=value

	def _set_volume(self,value):
		self.tts.Volume = value
		self._volume=value

	def _set_voice(self,value):
		if value>len(self.voiceNames):
			value=1
		self.tts=comtypesClient.CreateObject('sapi.SPVoice')
		self.tts.Voice(self.tts.GetVoices()[value-1])
		self._voice=value
		self.rate=self._rate
		self.volume=self._volume


	def speakText(self,text,wait=False,index=None):
		flags=constants.SVSFIsXML
		pitch=(self._pitch/2)-25
		if isinstance(index,int):
			bookmarkXML="<Bookmark Mark=\"%d\" />"%index
		else:
			bookmarkXML=""
		flags=constants.SVSFIsXML
		if wait is False:
			flags+=constants.SVSFlagsAsync
		self.tts.Speak("<pitch absmiddle=\"%s\">%s%s</pitch>"%(pitch,bookmarkXML,text),flags)

	def cancel(self):
		#if self.tts.Status.RunningState == 2:
		self.tts.Speak(None, 1|constants.SVSFPurgeBeforeSpeak)
