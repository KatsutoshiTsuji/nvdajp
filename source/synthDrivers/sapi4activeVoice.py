#synthDrivers/sapi4activeVoice.py
#A part of NonVisual Desktop Access (NVDA)
#Copyright (C) 2006-2008 NVDA Contributors <http://www.nvda-project.org/>
#This file is covered by the GNU General Public License.
#See the file COPYING for more details.

import os
import comtypes.client
import _winreg
import synthDriverHandler
import config
import globalVars
from logHandler import log
import nvwave

COM_CLASS = "ActiveVoice.ActiveVoice"

class SynthDriver(synthDriverHandler.SynthDriver):

	hasVoice=True
	hasRate=True
	hasPitch=True
	hasVolume=True

	name="sapi4activeVoice"
	description="Microsoft Speech API 4 (ActiveVoice.ActiveVoice)"

	@classmethod
	def _registerDll(cls):
		try:
			ret = os.system(r"regsvr32 /s %SystemRoot%\speech\xvoice.dll")
			return ret == 0
		except:
			pass
			return False

	@classmethod
	def check(cls):
		try:
			r=_winreg.OpenKey(_winreg.HKEY_CLASSES_ROOT,COM_CLASS)
			r.Close()
			return True
		except:
			pass
		return cls._registerDll()

	def initialize(self):
		try:
			self.check()
			self.tts=comtypes.client.CreateObject(COM_CLASS,)
			self._ttsEventObj=comtypes.client.GetEvents(self.tts,self)
			self.tts.InitAudioDestMM(nvwave.outputDeviceNameToID(config.conf["speech"]["outputDevice"], True))
			self.tts.CallBacksEnabled=1
			self.tts.Tagged=1
			self.tts.initialized=1
			self._lastIndex=None
			return True
		except:
			log.error("initialize", exc_info=True)
			return False

	def _get_voiceCount(self):
		return self.tts.CountEngines

	def getVoiceName(self,num):
		return self.tts.modeName(num)

	def terminate(self):
		del self.tts

	def _paramToPercent(self, current, min, max):
		return int(round(float(current - min) / (max - min) * 100))

	def _percentToParam(self, percent, min, max):
		return int(round(float(percent) / 100 * (max - min) + min))

	#Events

	def BookMark(self,x,y,z,markNum):
		self._lastIndex=markNum-1

	def _get_rate(self):
		return self._paramToPercent(self.tts.speed,self.tts.minSpeed,self.tts.maxSpeed)

	def _get_pitch(self):
		return self._paramToPercent(self.tts.pitch,self.tts.minPitch,self.tts.maxPitch)

	def _get_volume(self):
		return self._paramToPercent(self.tts.volumeLeft,self.tts.minVolumeLeft,self.tts.maxVolumeLeft)

	def _get_voice(self):
		return self.tts.currentMode

	def _get_lastIndex(self):
		return self._lastIndex

	def _set_rate(self,rate):
		# ViaVoice doesn't seem to like the speed being set to maximum.
		self.tts.speed=min(self._percentToParam(rate, self.tts.minSpeed, self.tts.maxSpeed), self.tts.maxSpeed - 1)
		self.tts.speak("")

	def _set_pitch(self,value):
		self.tts.pitch=self._percentToParam(value, self.tts.minPitch, self.tts.maxPitch)

	def _set_volume(self,value):
		self.tts.volumeLeft = self.tts.VolumeRight = self._percentToParam(value, self.tts.minVolumeLeft, self.tts.maxVolumeLeft)
		self.tts.speak("")

	def _set_voice(self,value):
		self.tts.initialized=0
		try:
			self.tts.select(value)
		except:
			pass
		self.tts.initialized=1
		try:
			self.tts.select(value)
		except:
			pass

	def speakText(self,text,index=None):
		text=text.replace("\\","\\\\")
		if isinstance(index,int) and index>=0:
			text="".join(["\\mrk=%d\\"%(index+1),text])
		self.tts.speak(text)

	def cancel(self):
		self.tts.audioReset()

	def pause(self,switch):
		if switch:
			self.tts.audioPause()
		else:
			self.tts.audioResume()
