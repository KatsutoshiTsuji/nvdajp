#NVDAObjects/MSHTML.py
#A part of NonVisual Desktop Access (NVDA)
#Copyright (C) 2006-2007 NVDA Contributors <http://www.nvda-project.org/>
#This file is covered by the GNU General Public License.
#See the file COPYING for more details.

import time
import ctypes
import comtypesClient
import comtypes.automation
import pythoncom
import win32com.client
import debug
import winUser
import IAccessibleHandler
from keyUtils import key, sendKey
import api
import speech
import controlTypes
from . import IAccessible
 
class MSHTML(IAccessible):

	def getDocumentObjectModel(self):
		domPointer=ctypes.POINTER(comtypes.automation.IDispatch)()
		wm=winUser.registerWindowMessage(u'WM_HTML_GETOBJECT')
		lresult=winUser.sendMessage(self.windowHandle,wm,0,0)
		res=ctypes.windll.oleacc.ObjectFromLresult(lresult,ctypes.byref(domPointer._iid_),0,ctypes.byref(domPointer))
		#We use pywin32 for large IDispatch interfaces since it handles them much better than comtypes
		o=pythoncom._univgw.interface(ctypes.cast(domPointer,ctypes.c_void_p).value,pythoncom.IID_IDispatch)
		t=o.GetTypeInfo()
		a=t.GetTypeAttr()
		oleRepr=win32com.client.build.DispatchItem(attr=a)
		return win32com.client.CDispatch(o,oleRepr)

	def _get_typeString(self):
		if self.isContentEditable:
			return IAccessibleHandler.getRoleName(IAccessibleHandler.ROLE_SYSTEM_TEXT)

	def _get_value(self):
		if self.isContentEditable:
			r=self.text_getLineOffsets(self.text_caretOffset)
			if r:
				return self.text_getText(r[0],r[1])
		return ""

	def _get_isContentEditable(self):
		if hasattr(self,'dom') and self.dom.activeElement.isContentEditable:
			return True
		else:
			return False

	def getOffsetBias(self):
		r=self.dom.selection.createRange().duplicate()
		r.move("textedit",-1)
		return ord(r.getBookmark()[2])

	def getLineNumBias(self):
		r=self.dom.selection.createRange().duplicate()
		r.move("textedit",-1)
		return ord(r.getBookmark()[8])

	def getBookmarkOffset(self,bookmark):
		lineNum=(ord(bookmark[8])-self.getLineNumBias())/2
		return ord(bookmark[2])-self.getOffsetBias()-lineNum

	def getBookmarkOffsets(self,bookmark):
		start=self.getBookmarkOffset(bookmark)
		if ord(bookmark[1])==3:
			lineNum=(ord(bookmark[8])-self.getLineNumBias())/2
			end=ord(bookmark[40])-self.getOffsetBias()-lineNum
		else:
			end=start
		return (start,end)

	def getDomRange(self,start,end):
		r=self.dom.selection.createRange().duplicate()
		r.move("textedit",-1)
		r.move("character",start)
		if end!=start:
			r.moveEnd("character",end-start)
		return r

	def _get_text_characterCount(self):
		if not hasattr(self,'dom'):
			return 0
		r=self.dom.selection.createRange().duplicate()
		r.expand("textedit")
		bookmark=r.getBookmark()
		return self.getBookmarkOffsets(bookmark)[1]

	def text_getText(self,start=None,end=None):
		if not hasattr(self,'dom'):
			return "\0"
		start=start if isinstance(start,int) else 0
		end=end if isinstance(end,int) else self.text_characterCount
		r=self.getDomRange(start,end)
		return r.text

	def _get_text_selectionCount(self):
		if not hasattr(self,'dom'):
			return 0
		bookmark=self.dom.selection.createRange().getBookmark()
		if ord(bookmark[1])==3:
			return 1
		else:
			return 0

	def text_getSelectionOffsets(self,index):
		if not hasattr(self,'dom') or (index!=0) or (self.text_selectionCount!=1):
			return None
		bookmark=self.dom.selection.createRange().getBookmark()
		return self.getBookmarkOffsets(bookmark)

	def _get_text_caretOffset(self):
		if not hasattr(self,'dom'):
			return 0
		bookmark=self.dom.selection.createRange().getBookmark()
		return self.getBookmarkOffset(bookmark)

	def _set_text_caretOffset(self,offset):
		if not hasattr(self,'dom'):
			return
		r=self.getDomRange(offset,offset)
		bookmark=r.getBookmark()
		self.dom.selection.createRange().moveToBookmark(bookmark)

	def text_getLineNumber(self,offset):
		r=self.getDomRange(offset,offset)
		return (ord(r.getBookmark()[8])-self.lineNumBias)/2

	def text_getLineOffsets(self,offset):
		if not hasattr(self,'dom'):
			return
		oldBookmark=self.dom.selection.createRange().getBookmark()
		r=self.getDomRange(offset,offset)
		self.dom.selection.createRange().moveToBookmark(r.getBookmark())
		sendKey(key("ExtendedEnd"))
		end=self.getBookmarkOffset(self.dom.selection.createRange().getBookmark())
		sendKey(key("ExtendedHome"))
		start=self.getBookmarkOffset(self.dom.selection.createRange().getBookmark())
		self.dom.selection.createRange().moveToBookmark(oldBookmark)
		return (start,end)

	def text_getNextLineOffsets(self,offset):
		if not hasattr(self,'dom'):
			return
		oldBookmark=self.dom.selection.createRange().getBookmark()
		r=self.getDomRange(offset,offset)
		self.dom.selection.createRange().moveToBookmark(r.getBookmark())
		sendKey(key("extendedDown"))
		sendKey(key("ExtendedEnd"))
		end=self.getBookmarkOffset(self.dom.selection.createRange().getBookmark())
		sendKey(key("ExtendedHome"))
		start=self.getBookmarkOffset(self.dom.selection.createRange().getBookmark())
		self.dom.selection.createRange().moveToBookmark(oldBookmark)
		if start>offset:
			return (start,end)
		else:
			return None

	def text_getPrevLineOffsets(self,offset):
		if not hasattr(self,'dom'):
			return
		oldBookmark=self.dom.selection.createRange().getBookmark()
		r=self.getDomRange(offset,offset)
		self.dom.selection.createRange().moveToBookmark(r.getBookmark())
		sendKey(key("extendedUp"))
		sendKey(key("ExtendedEnd"))
		end=self.getBookmarkOffset(self.dom.selection.createRange().getBookmark())
		sendKey(key("ExtendedHome"))
		start=self.getBookmarkOffset(self.dom.selection.createRange().getBookmark())
		self.dom.selection.createRange().moveToBookmark(oldBookmark)
		if end<=offset and start<offset:
			return (start,end)
		else:
			return None

	def text_getWordOffsets(self,offset):
		r=self.getDomRange(offset,offset+1)
		r.expand("word")
		return self.getBookmarkOffsets(r.getBookmark())

	def text_getNextWordOffsets(self,offset):
		r=self.getDomRange(offset,offset)
		r.move("word",1)
		r.expand("word")
		(start,end)=self.getBookmarkOffsets(r.getBookmark())
		if start>offset:
			return (start,end)
		else:
			return None

	def text_getPrevWordOffsets(self,offset):
		r=self.getDomRange(offset,offset)
		r.move("word",-1)
		r.expand("word")
		(start,end)=self.getBookmarkOffsets(r.getBookmark())
		if end<=offset and start<offset:
			return (start,end)
		else:
			return None

	def text_getSentenceOffsets(self,offset):
		r=self.getDomRange(offset,offset)
		r.expand("sentence")
		return self.getBookmarkOffsets(r.getBookmark())

	def text_getNextSentenceOffsets(self,offset):
		r=self.getDomRange(offset,offset)
		r.move("sentence",1)
		r.expand("sentence")
		(start,end)=self.getBookmarkOffsets(r.getBookmark())
		if start>offset:
			return (start,end)
		else:
			return None

	def text_getPrevSentenceOffsets(self,offset):
		r=self.getDomRange(offset,offset)
		r.move("sentence",-1)
		r.expand("sentence")
		(start,end)=self.getBookmarkOffsets(r.getBookmark())
		if end<=offset and start<offset:
			return (start,end)
		else:
			return None

	def text_getFieldOffsets(self,offset):
		r=self.text_getSentenceOffsets(offset)
		if r is None:
			r=self.text_getLineOffsets(offset)
		return r

	def text_getNextFieldOffsets(self,offset):
		r=self.text_getNextSentenceOffsets(offset)
		if r is None:
			r=self.text_getNextLineOffsets(offset)
		return r

	def text_getPrevFieldOffsets(self,offset):
		r=self.text_getPrevSentenceOffsets(offset)
		if r is None:
			r=self.text_getPrevLineOffsets(offset)
		return r

	def event_gainFocus(self):
		if self.IAccessibleRole==IAccessibleHandler.ROLE_SYSTEM_PANE and self.IAccessibleObjectID==-4:
			return
		self.dom=self.getDocumentObjectModel()
		self.lineNumBias=self.getLineNumBias()
		self.offsetBias=self.getOffsetBias()
		if self.dom.body.isContentEditable:
			self.role=controlTypes.ROLE_EDITABLETEXT
			if not api.isVirtualBufferPassThrough():
				api.toggleVirtualBufferPassThrough()
		IAccessible.event_gainFocus(self)

	def event_looseFocus(self):
		if hasattr(self,'dom'):
			del self.dom

	def script_text_moveByLine(self,keyPress,nextScript):
		sendKey(keyPress)
		if not hasattr(self,'dom'):
			return 
		oldBookmark=self.dom.selection.createRange().getBookmark()
		sendKey(key("extendedEnd"))
		end=self.dom.selection.createRange().duplicate()
		sendKey(key("extendedHome"))
		start=self.dom.selection.createRange().duplicate()
		start.setEndPoint("endToStart",end)
		self.dom.selection.createRange().moveToBookmark(oldBookmark)
		speech.speakText(start.text)

	def script_text_moveByCharacter(self,keyPress,nextScript):
		sendKey(keyPress)
		if not hasattr(self,'dom'):
			return 
		r=self.dom.selection.createRange().duplicate()
		r.expand("character")
		speech.speakSymbol(r.text)

	def script_text_moveByWord(self,keyPress,nextScript):
		sendKey(keyPress)
		if not hasattr(self,'dom'):
			return 
		r=self.dom.selection.createRange().duplicate()
		r.expand("word")
		speech.speakText(r.text)

	def script_text_backspace(self,keyPress,nextScript):
		if not hasattr(self,'dom'):
			return 
		r=self.dom.selection.createRange().duplicate()
		delta=r.move("character",-1)
		if delta<0:
			r.expand("character")
			delChar=r.text
		else:
			delChar=""
		sendKey(keyPress)
		speech.speakSymbol(delChar)

	def script_text_changeSelection(self,keyPress,nextScript):
		if not hasattr(self,'dom'):
			return 
		before=self.dom.selection.createRange().duplicate()
		sendKey(keyPress)
		after=self.dom.selection.createRange().duplicate()
		leftDelta=before.compareEndPoints("startToStart",after)
		rightDelta=before.compareEndPoints("endToEnd",after)
		afterLen=after.compareEndPoints("startToEnd",after)
		if afterLen==0:
			after.expand("character")
			speech.speakSymbol(after.text)
		elif leftDelta<0:
 			before.setEndPoint("endToStart",after)
			speech.speakMessage(_("unselected %s")%before.text)
		elif leftDelta>0:
 			after.setEndPoint("endToStart",before)
			speech.speakMessage(_("selected %s")%after.text)
		elif rightDelta>0:
 			before.setEndPoint("startToEnd",after)
			speech.speakMessage(_("unselected %s")%before.text)
		elif rightDelta<0:
 			after.setEndPoint("startToEnd",before)
			speech.speakMessage(_("selected %s")%after.text)

[MSHTML.bindKey(keyName,scriptName) for keyName,scriptName in [
	("ExtendedUp","text_moveByLine"),
	("ExtendedDown","text_moveByLine"),
	("ExtendedLeft","text_moveByCharacter"),
	("ExtendedRight","text_moveByCharacter"),
	("Control+ExtendedLeft","text_moveByWord"),
	("Control+ExtendedRight","text_moveByWord"),
	("Shift+ExtendedRight","text_changeSelection"),
	("Shift+ExtendedLeft","text_changeSelection"),
	("Shift+ExtendedHome","text_changeSelection"),
	("Shift+ExtendedEnd","text_changeSelection"),
	("Shift+ExtendedUp","text_changeSelection"),
	("Shift+ExtendedDown","text_changeSelection"),
	("Control+Shift+ExtendedLeft","text_changeSelection"),
	("Control+Shift+ExtendedRight","text_changeSelection"),
	("ExtendedHome","text_moveByCharacter"),
	("ExtendedEnd","text_moveByCharacter"),
	("control+extendedHome","text_moveByLine"),
	("control+extendedEnd","text_moveByLine"),
	("control+shift+extendedHome","text_changeSelection"),
	("control+shift+extendedEnd","text_changeSelection"),
	("ExtendedDelete","text_moveByCharacter"),
	("Back","text_backspace"),
]]
