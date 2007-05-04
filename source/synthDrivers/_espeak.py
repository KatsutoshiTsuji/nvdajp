import nvwave
import threading
import Queue
from ctypes import *

isSpeaking = False
lastIndex = None
bgQueue = None
player = None

#Parameter bounds
minRate=50
maxRate=350
minPitch=10
maxPitch=140

#event types
espeakEVENT_LIST_TERMINATED=0
espeakEVENT_WORD=1
espeakEVENT_SENTENCE=2
espeakEVENT_MARK=3
espeakEVENT_PLAY=4
espeakEVENT_END=5
espeakEVENT_MSG_TERMINATED=6

#position types
POS_CHARACTER=1
POS_WORD=2
POS_SENTENCE=3

#output types
AUDIO_OUTPUT_PLAYBACK=0
AUDIO_OUTPUT_RETRIEVAL=1
AUDIO_OUTPUT_SYNCHRONOUS=2
AUDIO_OUTPUT_SYNCH_PLAYBACK=3

#synth flags
espeakCHARS_AUTO=0
espeakCHARS_UTF8=1
espeakCHARS_8BIT=2
espeakCHARS_WCHAR=3
espeakSSML=0x10
espeakPHONEMES=0x100
espeakENDPAUSE=0x1000
espeakKEEP_NAMEDATA=0x2000

#speech parameters
espeakSILENCE=0
espeakRATE=1
espeakVOLUME=2
espeakPITCH=3
espeakRANGE=4
espeakPUNCTUATION=5
espeakCAPITALS=6
espeakEMPHASIS=7
espeakLINELENGTH=8
espeakVOICETYPE=9

#error codes
EE_OK=0
EE_INTERNAL_ERROR=-1
EE_BUFFER_FULL=1
EE_NOT_FOUND=2

class espeak_EVENT_id(Union):
	_fields_=[
		('number',c_int),
		('name',c_char_p),
	]

class espeak_EVENT(Structure):
	_fields_=[
		('type',c_int),
		('unique_identifier',c_uint),
		('text_position',c_int),
		('length',c_int),
		('audio_position',c_int),
		('sample',c_int),
		('user_data',c_void_p),
		('id',espeak_EVENT_id),
	]

class espeak_VOICE(Structure):
	_fields_=[
		('name',c_char_p),
		('languages',c_char_p),
		('identifier',c_char_p),
		('gender',c_byte),
		('age',c_byte),
		('variant',c_byte),
		('xx1',c_byte),
		('score',c_int),
		('spare',c_void_p),
	]

	def __eq__(self, other):
		return isinstance(other, type(self)) and addressof(self) == addressof(other)

 
t_espeak_callback=CFUNCTYPE(c_int,POINTER(c_short),c_int,POINTER(espeak_EVENT))

@t_espeak_callback
def callback(wav,numsamples,event):
	global player, isSpeaking, lastIndex
	lastIndex = event.contents.user_data
	if not wav:
		isSpeaking = False
		return 0
	if not isSpeaking:
		return 1
	if numsamples > 0:
		player.feed(string_at(wav, numsamples * sizeof(c_short)))
	return 0

espeakDLL=cdll.LoadLibrary(r"synthDrivers\espeak.dll")
espeakDLL.espeak_ListVoices.restype=POINTER(POINTER(espeak_VOICE))
espeakDLL.espeak_GetCurrentVoice.restype=POINTER(espeak_VOICE)

class BgThread(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
		self.setDaemon(True)

	def run(self):
		global bgQueue
		while True:
			func, args, kwargs = bgQueue.get()
			if not func:
				# Terminate.
				bgQueue = None
				espeakDLL.espeak_Terminate()
				break
			func(*args, **kwargs)
			bgQueue.task_done()

def _bgExec(func, *args, **kwargs):
	global bgQueue
	bgQueue.put((func, args, kwargs))

def _speakBg(msg, index=None):
	global isSpeaking
	uniqueID=c_int()
	isSpeaking = True
	espeakDLL.espeak_Synth(unicode(msg),0,0,0,0,espeakCHARS_WCHAR,byref(uniqueID),index)

def speak(msg, index=None, wait=False):
	global bgQueue
	_bgExec(_speakBg, msg, index)
	if wait:
		bgQueue.join()

def stop():
	global isSpeaking, bgQueue
	# Kill all speech from now.
	# We still want parameter changes to occur, so requeue them.
	params = []
	while not bgQueue.empty():
		item = bgQueue.get_nowait()
		if item[0] == espeakDLL.espeak_SetParameter:
			params.append(item)
	for item in params:
		bgQueue.put(item)
	isSpeaking = False
	player.stop()

def setParameter(param,value,relative):
	_bgExec(espeakDLL.espeak_SetParameter,param,value,relative)

def getParameter(param,current):
	return espeakDLL.espeak_GetParameter(param,current)

def getVoiceList():
	begin=espeakDLL.espeak_ListVoices(None)
	count=0
	voiceList=[]
	while True:
		if not begin[count]: break
 		voiceList.append(begin[count].contents)
		count+=1
	return voiceList

def getCurrentVoice():
	voice =  espeakDLL.espeak_GetCurrentVoice()
	if voice:
		return voice.contents
	else:
		return None

def setVoice(voice):
	# For some weird reason, espeak_EspeakSetVoiceByProperties throws an integer divide by zero exception.
	espeakDLL.espeak_SetVoiceByName(voice.identifier)

def setVoiceByName(name):
	espeakDLL.espeak_SetVoiceByName(name)

def initialize():
	global espeakDLL, bgQueue, player
	espeakDLL.espeak_Initialize(AUDIO_OUTPUT_SYNCHRONOUS,300,"synthDrivers")
	player = nvwave.WavePlayer(channels=1, samplesPerSec=22050, bitsPerSample=16)
	espeakDLL.espeak_SetSynthCallback(callback)
	bgQueue = Queue.Queue()
	BgThread().start()

def terminate():
	global bgQueue
	bgQueue.put((None, None, None))
	player.close()
