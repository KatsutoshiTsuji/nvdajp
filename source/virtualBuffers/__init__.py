import ctypes
import weakref
import time
import os
import winsound
import XMLFormatting
import baseObject
from keyUtils import sendKey
from scriptHandler import isScriptWaiting
import speech
import NVDAObjects
import winUser
import api
import sayAllHandler
import controlTypes
import textHandler
#Before importing virtualBuffer_lib, force ctypes to use virtualBuffer.dll from the lib dir, not the current dir
ctypes.cdll.virtualBuffer=ctypes.cdll.LoadLibrary('lib\\virtualBuffer.dll')
from virtualBuffer_lib import *
import globalVars
import config
import api
import cursorManager
from gui import scriptUI
import virtualBufferHandler

class VirtualBufferTextInfo(NVDAObjects.NVDAObjectTextInfo):

	def _getLineNumFromOffset(offset):
		#virtualBuffers have no concept of line numbers
		return 0

	def _getSelectionOffsets(self):
		start,end=VBufClient_getBufferSelectionOffsets(self.obj.VBufHandle)
		return (start,end)

	def _setSelectionOffsets(self,start,end):
		VBufClient_setBufferSelectionOffsets(self.obj.VBufHandle,start,end)

	def _getCaretOffset(self):
		return self._getSelectionOffsets()[0]

	def _setCaretOffset(self,offset):
		return self._setSelectionOffsets(offset,offset)

	def _getStoryLength(self):
		return VBufClient_getBufferTextLength(self.obj.VBufHandle)

	def _getTextRange(self,start,end):
		text=VBufClient_getBufferTextByOffsets(self.obj.VBufHandle,start,end)
		return text

	def _getWordOffsets(self,offset):
		#Use VBufClient_getBufferLineOffsets with out screen layout to find out the range of the current field
		line_startOffset,line_endOffset=VBufClient_getBufferLineOffsets(self.obj.VBufHandle,offset,0,False)
		word_startOffset,word_endOffset=super(VirtualBufferTextInfo,self)._getWordOffsets(offset)
		return (max(line_startOffset,word_startOffset),min(line_endOffset,word_endOffset))

	def _getLineOffsets(self,offset):
		return VBufClient_getBufferLineOffsets(self.obj.VBufHandle,offset,config.conf["virtualBuffers"]["maxLineLength"],config.conf["virtualBuffers"]["useScreenLayout"])

	def _getParagraphOffsets(self,offset):
		return VBufClient_getBufferLineOffsets(self.obj.VBufHandle,offset,0,True)

	def _normalizeControlField(self,attrs):
		return attrs

	def getInitialFields(self,formatConfig=None):
		XMLContext=VBufClient_getXMLContextAtBufferOffset(self.obj.VBufHandle,self._startOffset)
		ancestry=XMLFormatting.XMLContextParser().parse(XMLContext)
		for index in xrange(len(ancestry)):
			ancestry[index]=self._normalizeControlField(ancestry[index])
		return ancestry

	def getTextWithFields(self,formatConfig=None):
		start=self._startOffset
		end=self._endOffset
		XMLText=VBufClient_getXMLBufferTextByOffsets(self.obj.VBufHandle,start,end)
		commandList=XMLFormatting.RelativeXMLParser().parse(XMLText)
		for index in xrange(len(commandList)):
			if isinstance(commandList[index],textHandler.FieldCommand) and isinstance(commandList[index].field,textHandler.ControlField):
				commandList[index].field=self._normalizeControlField(commandList[index].field)
		return commandList

	def _getLineNumFromOffset(self, offset):
		return None

	def getXMLFieldSpeech(self,attrs,fieldType,extraDetail=False,reason=None):
		return speech.getXMLFieldSpeech(self,attrs,fieldType,extraDetail=extraDetail,reason=reason)

class VirtualBuffer(cursorManager.CursorManager):

	def __init__(self,rootNVDAObject,backendLibPath=None,TextInfo=VirtualBufferTextInfo):
		self.backendLibPath=os.path.abspath(backendLibPath)
		self.TextInfo=TextInfo
		self.rootNVDAObject=rootNVDAObject
		super(VirtualBuffer,self).__init__()
		self.VBufHandle=None
		self.passThrough=False
		self.rootWindowHandle=self.rootNVDAObject.windowHandle
		self.rootID=0

	def loadBuffer(self):
		self.VBufHandle=VBufClient_createBuffer(self.rootWindowHandle,self.rootID,self.backendLibPath)

	def unloadBuffer(self):
		if self.VBufHandle is not None:
			VBufClient_destroyBuffer(self.VBufHandle)
			self.VBufHandle=None

	def makeTextInfo(self,position):
		return self.TextInfo(self,position)

	def isNVDAObjectInVirtualBuffer(self,obj):
		pass

	def isAlive(self):
		pass

	def _get_windowHandle(self):
		return self.rootNVDAObject.windowHandle

	def event_virtualBuffer_firstEnter(self):
		"""Triggered the first time this virtual buffer is entered.
		"""
		speech.cancelSpeech()
		virtualBufferHandler.reportPassThrough(self)
		speech.speakObjectProperties(self.rootNVDAObject,name=True)
		info=self.makeTextInfo(textHandler.POSITION_CARET)
		sayAllHandler.readText(info,sayAllHandler.CURSOR_CARET)

	def _calculateLineBreaks(self,text):
		maxLineLength=config.conf["virtualBuffers"]["maxLineLength"]
		lastBreak=0
		lineBreakOffsets=[]
		for offset in range(len(text)):
			if offset-lastBreak>maxLineLength and offset>0 and text[offset-1].isspace() and not text[offset].isspace():
				lineBreakOffsets.append(offset)
				lastBreak=offset
		return lineBreakOffsets

	def _activateField(self,docHandle,ID):
		pass

	def _activateContextMenuForField(self,docHandle,ID):
		pass

	def _caretMovedToField(self,dochandle,ID):
		pass

	def script_activatePosition(self,keyPress):
		if self.VBufHandle is None:
			return sendKey(keyPress)
		start,end=VBufClient_getBufferSelectionOffsets(self.VBufHandle)
		docHandle,ID=VBufClient_getFieldIdentifierFromBufferOffset(self.VBufHandle,start)
		self._activateField(docHandle,ID)
	script_activatePosition.__doc__ = _("activates the current object in the virtual buffer")

	def _caretMovementScriptHelper(self, *args, **kwargs):
		if self.VBufHandle is None:
			return 
		noKeyWaiting=not isScriptWaiting()
		if noKeyWaiting:
			oldDocHandle,oldID=VBufClient_getFieldIdentifierFromBufferOffset(self.VBufHandle,self.selection._startOffset)
		super(VirtualBuffer, self)._caretMovementScriptHelper(*args, **kwargs)
		if noKeyWaiting:
			docHandle,ID=VBufClient_getFieldIdentifierFromBufferOffset(self.VBufHandle,self.selection._startOffset)
			if ID!=0 and (docHandle!=oldDocHandle or ID!=oldID):
				self._caretMovedToField(docHandle,ID)

	def script_refreshBuffer(self,keyPress):
		if self.VBufHandle is None:
			return sendKey(keyPress)
		self.unloadBuffer()
		self.loadBuffer()
		speech.speakMessage(_("Refreshed"))

	def script_toggleScreenLayout(self,keyPress):
		config.conf["virtualBuffers"]["useScreenLayout"]=not config.conf["virtualBuffers"]["useScreenLayout"]
		onOff=_("on") if config.conf["virtualBuffers"]["useScreenLayout"] else _("off")
		speech.speakMessage(_("use screen layout %s")%onOff)

	def _searchableAttributesForNodeType(self,nodeType):
		pass

	def _iterNodesByType(self,nodeType,direction="next",startOffset=-1):
		attribs=self._searchableAttribsForNodeType(nodeType)
		if not attribs:
			return

		while True:
			try:
				docHandle,ID=VBufClient_findBufferFieldIdentifierByProperties(self.VBufHandle,direction,startOffset,attribs)
			except:
				return
			if not ID:
				continue

			startOffset,endOffset=VBufClient_getBufferOffsetsFromFieldIdentifier(self.VBufHandle,docHandle,ID)
			yield docHandle, ID, startOffset, endOffset

	def _quickNavScript(self,keyPress, nodeType, direction, errorMessage, readUnit):
		if self.VBufHandle is None:
			return sendKey(keyPress)
		startOffset, endOffset=VBufClient_getBufferSelectionOffsets(self.VBufHandle)
		try:
			docHandle, ID, startOffset, endOffset = self._iterNodesByType(nodeType, direction, startOffset).next()
		except StopIteration:
			speech.speakMessage(errorMessage)
			return
		info = self.makeTextInfo(textHandler.Offsets(startOffset, endOffset))
		if readUnit:
			fieldInfo = info.copy()
			info.collapse()
			info.move(readUnit, 1, endPoint="end")
			if info.compareEndPoints(fieldInfo, "endToEnd") > 0:
				# We've expanded past the end of the field, so limit to the end of the field.
				info.setEndPoint(fieldInfo, "endToEnd")
		info.updateCaret()
		speech.speakTextInfo(info, reason=speech.REASON_FOCUS)
		self._caretMovedToField(docHandle, ID)

	@classmethod
	def addQuickNav(cls, nodeType, key, nextDoc, nextError, prevDoc, prevError, readUnit=None):
		scriptSuffix = nodeType[0].upper() + nodeType[1:]
		scriptName = "next%s" % scriptSuffix
		funcName = "script_%s" % scriptName
		script = lambda self,keyPress: self._quickNavScript(keyPress, nodeType, "next", nextError, readUnit)
		script.__doc__ = nextDoc
		script.__name__ = funcName
		setattr(cls, funcName, script)
		cls.bindKey(key, scriptName)
		scriptName = "previous%s" % scriptSuffix
		funcName = "script_%s" % scriptName
		script = lambda self,keyPress: self._quickNavScript(keyPress, nodeType, "previous", prevError, readUnit)
		script.__doc__ = prevDoc
		script.__name__ = funcName
		setattr(cls, funcName, script)
		cls.bindKey("shift+%s" % key, scriptName)

	def script_linksList(self,keyPress):
		if self.VBufHandle is None:
			return

		nodes = []
		caretOffset, _ignored = VBufClient_getBufferSelectionOffsets(self.VBufHandle)
		defaultIndex = None
		for docHandle, ID, startOffset, endOffset in self._iterNodesByType("link"):
			if defaultIndex is None:
				if startOffset <= caretOffset and caretOffset < endOffset:
					# The caret is inside this link, so make it the default selection.
					defaultIndex = len(nodes)
				elif startOffset > caretOffset:
					# The caret wasn't inside a link, so set the default selection to be the next link.
					defaultIndex = len(nodes)
			text = self.makeTextInfo(textHandler.Offsets(startOffset,endOffset)).text
			nodes.append((text, docHandle, ID, startOffset, endOffset))

		def action(args):
			if args is None:
				return
			activate, index, text = args
			text, docHandle, ID, startOffset, endOffset = nodes[index]
			if activate:
				self._activateField(docHandle, ID)
			else:
				info=self.makeTextInfo(textHandler.Offsets(startOffset,endOffset))
				info.updateCaret()
				speech.cancelSpeech()
				speech.speakTextInfo(info,reason=speech.REASON_FOCUS)
				self._caretMovedToField(docHandle,ID)

		scriptUI.LinksListDialog(choices=[node[0] for node in nodes], default=defaultIndex if defaultIndex is not None else 0, callback=action).run()
	script_linksList.__doc__ = _("displays a list of links")

[VirtualBuffer.bindKey(keyName,scriptName) for keyName,scriptName in [
	("Return","activatePosition"),
	("Space","activatePosition"),
	("NVDA+f5","refreshBuffer"),
	("NVDA+v","toggleScreenLayout"),
	("NVDA+f7","linksList"),
]]

# Add quick navigation scripts.
qn = VirtualBuffer.addQuickNav
qn("heading", key="h", nextDoc=_("moves to the next heading"), nextError=_("no next heading"),
	prevDoc=_("moves to the previous heading"), prevError=_("no previous heading"))
qn("heading1", key="1", nextDoc=_("moves to the next heading at level 1"), nextError=_("no next heading at level 1"),
	prevDoc=_("moves to the previous heading at level 1"), prevError=_("no previous heading at level 1"))
qn("heading2", key="2", nextDoc=_("moves to the next heading at level 2"), nextError=_("no next heading at level 2"),
	prevDoc=_("moves to the previous heading at level 2"), prevError=_("no previous heading at level 2"))
qn("heading3", key="3", nextDoc=_("moves to the next heading at level 3"), nextError=_("no next heading at level 3"),
	prevDoc=_("moves to the previous heading at level 3"), prevError=_("no previous heading at level 3"))
qn("heading4", key="4", nextDoc=_("moves to the next heading at level 4"), nextError=_("no next heading at level 4"),
	prevDoc=_("moves to the previous heading at level 4"), prevError=_("no previous heading at level 4"))
qn("heading5", key="5", nextDoc=_("moves to the next heading at level 5"), nextError=_("no next heading at level 5"),
	prevDoc=_("moves to the previous heading at level 5"), prevError=_("no previous heading at level 5"))
qn("heading6", key="6", nextDoc=_("moves to the next heading at level 6"), nextError=_("no next heading at level 6"),
	prevDoc=_("moves to the previous heading at level 6"), prevError=_("no previous heading at level 6"))
qn("table", key="t", nextDoc=_("moves to the next table"), nextError=_("no next table"),
	prevDoc=_("moves to the previous table"), prevError=_("no previous table"), readUnit=textHandler.UNIT_LINE)
qn("link", key="k", nextDoc=_("moves to the next link"), nextError=_("no next link"),
	prevDoc=_("moves to the previous link"), prevError=_("no previous link"))
qn("visitedLink", key="v", nextDoc=_("moves to the next visited link"), nextError=_("no next visited link"),
	prevDoc=_("moves to the previous visited link"), prevError=_("no previous visited link"))
qn("unvisitedLink", key="u", nextDoc=_("moves to the next unvisited link"), nextError=_("no next unvisited link"),
	prevDoc=_("moves to the previous unvisited link"), prevError=_("no previous unvisited link"))
qn("formField", key="f", nextDoc=_("moves to the next form field"), nextError=_("no next form field"),
	prevDoc=_("moves to the previous form field"), prevError=_("no previous form field"), readUnit=textHandler.UNIT_LINE)
qn("list", key="l", nextDoc=_("moves to the next list"), nextError=_("no next list"),
	prevDoc=_("moves to the previous list"), prevError=_("no previous list"), readUnit=textHandler.UNIT_LINE)
qn("listItem", key="i", nextDoc=_("moves to the next list item"), nextError=_("no next list item"),
	prevDoc=_("moves to the previous list item"), prevError=_("no previous list item"))
qn("button", key="b", nextDoc=_("moves to the next button"), nextError=_("no next button"),
	prevDoc=_("moves to the previous button"), prevError=_("no previous button"))
qn("edit", key="e", nextDoc=_("moves to the next edit field"), nextError=_("no next edit field"),
	prevDoc=_("moves to the previous edit field"), prevError=_("no previous edit field"), readUnit=textHandler.UNIT_LINE)
qn("frame", key="m", nextDoc=_("moves to the next frame"), nextError=_("no next frame"),
	prevDoc=_("moves to the previous frame"), prevError=_("no previous frame"), readUnit=textHandler.UNIT_LINE)
qn("separator", key="s", nextDoc=_("moves to the next separator"), nextError=_("no next separator"),
	prevDoc=_("moves to the previous separator"), prevError=_("no previous separator"))
qn("radioButton", key="r", nextDoc=_("moves to the next radio button"), nextError=_("no next radio button"),
	prevDoc=_("moves to the previous radio button"), prevError=_("no previous radio button"))
qn("comboBox", key="c", nextDoc=_("moves to the next combo box"), nextError=_("no next combo box"),
	prevDoc=_("moves to the previous combo box"), prevError=_("no previous combo box"))
qn("checkBox", key="x", nextDoc=_("moves to the next check box"), nextError=_("no next check box"),
	prevDoc=_("moves to the previous check box"), prevError=_("no previous check box"))
qn("graphic", key="g", nextDoc=_("moves to the next graphic"), nextError=_("no next graphic"),
	prevDoc=_("moves to the previous graphic"), prevError=_("no previous graphic"))
qn("blockQuote", key="q", nextDoc=_("moves to the next block quote"), nextError=_("no next block quote"),
	prevDoc=_("moves to the previous block quote"), prevError=_("no previous block quote"))
del qn
