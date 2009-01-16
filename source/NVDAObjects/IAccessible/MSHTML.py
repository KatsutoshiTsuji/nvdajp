#NVDAObjects/MSHTML.py
#A part of NonVisual Desktop Access (NVDA)
#Copyright (C) 2006-2007 NVDA Contributors <http://www.nvda-project.org/>
#This file is covered by the GNU General Public License.
#See the file COPYING for more details.

import time
import ctypes
import comtypes.client
import comtypes.automation
from comInterfaces.servprov import IServiceProvider
import winUser
import globalVars
import IAccessibleHandler
from keyUtils import key, sendKey
import api
import textHandler
import speech
import controlTypes
from . import IAccessible
import NVDAObjects
import virtualBufferHandler

lastMSHTMLEditGainFocusTimeStamp=0


IID_IHTMLElement=comtypes.GUID('{3050F1FF-98B5-11CF-BB82-00AA00BDCE0B}')
IID_DispHTMLGenericElement=comtypes.GUID('{3050F563-98B5-11CF-BB82-00AA00BDCE0B}')
IID_DispHTMLTextAreaElement=comtypes.GUID('{3050F521-98B5-11CF-BB82-00AA00BDCE0B}')
IID_IHTMLInputTextElement=comtypes.GUID('{3050F2A6-98B5-11CF-BB82-00AA00BDCE0B}')

class MSHTMLTextInfo(textHandler.TextInfo):

	def _getRangeOffsets(self):
		mark=self._rangeObj.getBookmark()
		lineNum=(ord(mark[8])-self.obj._textRangeLineNumBias)/2
		start=(ord(mark[2])-self.obj._textRangeOffsetBias)-lineNum
		if ord(mark[1])==3:
			end=(ord(mark[40])-self.obj._textRangeOffsetBias)-lineNum
		else:
			end=start
		return [start,end]

	def _expandToLine(self,textRange):
		oldSelMark=self.obj.domElement.document.selection.createRange().getBookmark()
		curMark=textRange.getBookmark()
		self.obj.domElement.document.selection.createRange().moveToBookmark(curMark)
		api.processPendingEvents()
		sendKey(key("ExtendedEnd"))
		api.processPendingEvents()
		textRange.setEndPoint("endToEnd",self.obj.domElement.document.selection.createRange())
		sendKey(key("ExtendedHome"))
		api.processPendingEvents()
		textRange.setEndPoint("startToStart",self.obj.domElement.document.selection.createRange())
		self.obj.domElement.document.selection.createRange().moveToBookmark(oldSelMark)

	def __init__(self,obj,position,_rangeObj=None):
		super(MSHTMLTextInfo,self).__init__(obj,position)
		if self.obj.domElement.uniqueID!=self.obj.domElement.document.activeElement.uniqueID:
			raise RuntimeError("Only works with currently selected element")
		if _rangeObj:
			self._rangeObj=_rangeObj.duplicate()
			return
		self._rangeObj=self.obj.domElement.document.selection.createRange().duplicate()
		if position==textHandler.POSITION_SELECTION:
			pass
		elif position==textHandler.POSITION_CARET:
			self._rangeObj.collapse()
		elif position==textHandler.POSITION_FIRST:
			self._rangeObj.move("textedit",-1)
		elif position==textHandler.POSITION_LAST:
			self._rangeObj.expand("textedit")
			self.collapse(True)
			self._rangeObj.move("character",-1)
		elif isinstance(position,textHandler.Bookmark):
			if position.infoClass==self.__class__:
				self._rangeObj.moveToBookmark(position.data)
			else:
				raise TypeError("Bookmark was for %s type, not for %s type"%(position.infoClass.__name__,self.__class__.__name__))
		else:
			raise NotImplementedError("position: %s"%position)

	def expand(self,unit):
		if unit==textHandler.UNIT_LINE and self.basePosition not in [textHandler.POSITION_SELECTION,textHandler.POSITION_CARET]:
			unit=textHandler.UNIT_SENTENCE
		if unit==textHandler.UNIT_READINGCHUNK:
			unit=textHandler.UNIT_SENTENCE
		if unit in [textHandler.UNIT_CHARACTER,textHandler.UNIT_WORD,textHandler.UNIT_SENTENCE,textHandler.UNIT_PARAGRAPH]:
			self._rangeObj.expand(unit)
		elif unit==textHandler.UNIT_LINE:
			self._expandToLine(self._rangeObj)
		elif unit==textHandler.UNIT_STORY:
			self._rangeObj.expand("textedit")
		else:
			raise NotImplementedError("unit: %s"%unit)

	def _get_isCollapsed(self):
		if self._rangeObj.compareEndPoints("startToEnd",self._rangeObj)==0:
			return True
		else:
			return False


	def collapse(self,end=False):
		self._rangeObj.collapse(not end)

	def copy(self):
		return self.__class__(self.obj,None,_rangeObj=self._rangeObj.duplicate())

	def compareEndPoints(self,other,which):
		return self._rangeObj.compareEndPoints(which,other._rangeObj)

	def setEndPoint(self,other,which):
		self._rangeObj.setEndPoint(which,other._rangeObj)

	def _get_text(self):
		text=self._rangeObj.text
		if not text:
			text=""
		return text


	def move(self,unit,direction, endPoint=None):
		if unit in [textHandler.UNIT_READINGCHUNK,textHandler.UNIT_LINE]:
			unit=textHandler.UNIT_SENTENCE
		if unit==textHandler.UNIT_STORY:
			unit="textedit"
		if endPoint=="start":
			moveFunc=self._rangeObj.moveStart
		elif endPoint=="end":
			moveFunc=self._rangeObj.moveEnd
		else:
			moveFunc=self._rangeObj.move
		res=moveFunc(unit,direction)
		return res

	def updateCaret(self):
		self._rangeObj.select()

	def updateSelection(self):
		self._rangeObj.select()

	def _get_bookmark(self):
		return textHandler.Bookmark(self.__class__,self._rangeObj.getBookmark())

class MSHTML(IAccessible):

	def __init__(self,*args,**kwargs):
		super(MSHTML,self).__init__(*args,**kwargs)
		self.domElement=self.getDOMElementFromIAccessible()

	def getDOMElementFromIAccessible(self):
		s=self.IAccessibleObject.QueryInterface(IServiceProvider)
		interfaceAddress=s.QueryService(ctypes.byref(IID_IHTMLElement),ctypes.byref(comtypes.automation.IDispatch._iid_))
		ptr=ctypes.POINTER(comtypes.automation.IDispatch)(interfaceAddress)
		return comtypes.client.dynamic.Dispatch(ptr)

	def _get_value(self):
		if self.IAccessibleRole==IAccessibleHandler.ROLE_SYSTEM_PANE:
			return ""
		else:
			return super(MSHTML,self)._get_value()


	def _get_isContentEditable(self):
		if hasattr(self,'domElement'): 
			try:
				return bool(self.domElement.isContentEditable)
			except:
				return False
		else:
			return False

	def event_gainFocus(self):
		if self.isContentEditable:
			biasRange=self.domElement.document.selection.createRange().duplicate()
			biasRange.move("textedit",-1)
			biasMark=biasRange.getBookmark()
			self._textRangeLineNumBias=ord(biasMark[8])
			self._textRangeOffsetBias=ord(biasMark[2])
			self.TextInfo=MSHTMLTextInfo
			self.role=controlTypes.ROLE_EDITABLETEXT
		else:
			vbuf=self.virtualBuffer
			if vbuf and vbuf.passThrough:
				vbuf.passThrough=True
				virtualBufferHandler.reportPassThrough(vbuf)
		IAccessible.event_gainFocus(self)

	def reportFocus(self):
		global lastMSHTMLEditGainFocusTimeStamp
		timeStamp=time.time()
		if self.isContentEditable and (timeStamp-lastMSHTMLEditGainFocusTimeStamp)>0.5:
			super(MSHTML,self).reportFocus()
		lastMSHTMLEditGainFocusTimeStamp=timeStamp

	def event_loseFocus(self):
		if hasattr(self,'domElement'):
			self.TextInfo=NVDAObjects.NVDAObjectTextInfo

[MSHTML.bindKey(keyName,scriptName) for keyName,scriptName in [
	("ExtendedUp","moveByLine"),
	("ExtendedDown","moveByLine"),
	("ExtendedLeft","moveByCharacter"),
	("ExtendedRight","moveByCharacter"),
	("Control+ExtendedLeft","moveByWord"),
	("Control+ExtendedRight","moveByWord"),
	("Shift+ExtendedRight","changeSelection"),
	("Shift+ExtendedLeft","changeSelection"),
	("Shift+ExtendedHome","changeSelection"),
	("Shift+ExtendedEnd","changeSelection"),
	("Shift+ExtendedUp","changeSelection"),
	("Shift+ExtendedDown","changeSelection"),
	("Control+Shift+ExtendedLeft","changeSelection"),
	("Control+Shift+ExtendedRight","changeSelection"),
	("ExtendedHome","moveByCharacter"),
	("ExtendedEnd","moveByCharacter"),
	("control+extendedHome","moveByLine"),
	("control+extendedEnd","moveByLine"),
	("control+shift+extendedHome","changeSelection"),
	("control+shift+extendedEnd","changeSelection"),
	("ExtendedDelete","moveByCharacter"),
	("Back","backspace"),
]]
