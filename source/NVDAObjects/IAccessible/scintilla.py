import ctypes
import debug
import speech
import text
import winKernel
import winUser
import controlTypes
from . import IAccessible 
from .. import NVDAObjectTextInfo

#Window messages
SCI_GETTEXTRANGE=2162
SCI_GETTEXT=2182
SCI_GETTEXTLENGTH=2183
SCI_GETLENGTH=2006
SCI_GETCURRENTPOS=2008
SCI_GETANCHOR=2009
SCI_GETLINEENDPOSITION=2136
SCI_GETLINECOUNT=2154
SCI_LINEFROMPOSITION=2166
SCI_POSITIONFROMLINE=2167
SCI_GETSTYLEAT=2010
SCI_STYLEGETFONT=2486
SCI_STYLEGETSIZE=2485
SCI_STYLEGETBOLD=2483
SCI_STYLEGETITALIC=2484
SCI_STYLEGETUNDERLINE=2488
SCI_WORDSTARTPOSITION=2266
SCI_WORDENDPOSITION=2267

#constants
STYLE_DEFAULT=32

class CharacterRangeStruct(ctypes.Structure):
	_fields_=[
		('cpMin',ctypes.c_long),
		('cpMax',ctypes.c_long),
	]

class TextRangeStruct(ctypes.Structure):
	_fields_=[
		('chrg',CharacterRangeStruct),
		('lpstrText',ctypes.c_char_p),
	]

class ScintillaTextInfo(NVDAObjectTextInfo):

	def _getSelOffsets(self):
		curOffset=winUser.sendMessage(self.obj.windowHandle,SCI_GETCURRENTPOS,0,0)
		curAnchor=winUser.sendMessage(self.obj.windowHandle,SCI_GETANCHOR,0,0)
		return [min(curOffset,curAnchor),max(curOffset,curAnchor)]

	def _getStoryText(self):
		if not hasattr(self,'_storyText'):
			storyLength=self._getStoryLength()
			self._storyText=self._getTextRange(0,storyLength)
		return self._storyText

	def _getStoryLength(self):
		if not hasattr(self,'_storyLength'):
			self._storyLength=winUser.sendMessage(self.obj.windowHandle,SCI_GETTEXTLENGTH,0,0)
		return self._storyLength

	def _getLineCount(self):
		return winUser.sendMessage(self.obj.windowHandle,SCI_GETLINECOUNT,0,0)

	def _getTextRange(self,start,end):
		bufLen=(end-start)+1
		textRange=TextRangeStruct()
		textRange.chrg.cpMin=start
		textRange.chrg.cpMax=end
		processHandle=winKernel.openProcess(winKernel.PROCESS_VM_OPERATION|winKernel.PROCESS_VM_READ|winKernel.PROCESS_VM_WRITE,False,self.obj.windowProcessID)
		internalBuf=winKernel.virtualAllocEx(processHandle,None,bufLen,winKernel.MEM_COMMIT,winKernel.PAGE_READWRITE)
		textRange.lpstrText=internalBuf
		internalTextRange=winKernel.virtualAllocEx(processHandle,None,ctypes.sizeof(textRange),winKernel.MEM_COMMIT,winKernel.PAGE_READWRITE)
		winKernel.writeProcessMemory(processHandle,internalTextRange,ctypes.byref(textRange),ctypes.sizeof(textRange),None)
		winUser.sendMessage(self.obj.windowHandle,SCI_GETTEXTRANGE,0,internalTextRange)
		winKernel.virtualFreeEx(processHandle,internalTextRange,0,winKernel.MEM_RELEASE)
		buf=ctypes.create_string_buffer(bufLen)
		winKernel.readProcessMemory(processHandle,internalBuf,buf,bufLen,None)
		winKernel.virtualFreeEx(processHandle,internalBuf,0,winKernel.MEM_RELEASE)
		return buf.value

	def _getWordOffsets(self,offset):
		start=winUser.sendMessage(self.obj.windowHandle,SCI_WORDSTARTPOSITION,offset,0)
		end=winUser.sendMessage(self.obj.windowHandle,SCI_WORDENDPOSITION,offset,0)
		return [start,end]

	def _lineNumFromOffset(self,offset):
		return winUser.sendMessage(self.obj.windowHandle,SCI_LINEFROMPOSITION,offset,0)

	def _getLineOffsets(self,offset):
		lineNum=self._lineNumFromOffset(offset)
		start=winUser.sendMessage(self.obj.windowHandle,SCI_POSITIONFROMLINE,lineNum,0)
		end=winUser.sendMessage(self.obj.windowHandle,SCI_GETLINEENDPOSITION,lineNum,0)
		return [start,end]

	def _getParagraphOffsets(self,offset):
		return super(EditTextInfo,self)._getLineOffsets(offset)

#The Scintilla NVDA object, inherists the generic MSAA NVDA object
class Scintilla(IAccessible):

	TextInfo=ScintillaTextInfo

#The name of the object is gotten by the standard way of getting a window name, can't use MSAA name (since it contains all the text)
	def _get_name(self):
		return winUser.getWindowText(self.windowHandle)

#The role of the object should be editable text
	def _get_role(self):
		return controlTypes.ROLE_EDITABLETEXT

#The value of the object should be the current line of the text
	def _get_value(self):
		info=self.makeTextInfo(text.POSITION_CARET)
		info.expand(text.UNIT_LINE)
		return info.text

#We want all the standard text editing key commands to be handled by NVDA
[Scintilla.bindKey(keyName,scriptName) for keyName,scriptName in [
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
	("ExtendedDelete","delete"),
	("Back","backspace"),
]]
