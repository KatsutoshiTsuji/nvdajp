#NVDAObjects/winEdit.py
#A part of NonVisual Desktop Access (NVDA)
#Copyright (C) 2006-2007 Michael Curran <mick@kulgan.net>
#This file is covered by the GNU General Public License.
#See the file COPYING for more details.

import struct
import ctypes
import audio
import debug
import winUser
from keyUtils import key
import IAccessibleHandler
import IAccessible

class NVDAObject_winEdit(IAccessible.NVDAObject_IAccessible):

	def __init__(self,*args,**vars):
		IAccessible.NVDAObject_IAccessible.__init__(self,*args,**vars)
		self.registerScriptKeys({
			key("ExtendedUp"):self.script_text_moveByLine,
			key("ExtendedDown"):self.script_text_moveByLine,
			key("ExtendedLeft"):self.script_text_moveByCharacter,
			key("ExtendedRight"):self.script_text_moveByCharacter,
			key("Control+ExtendedLeft"):self.script_text_moveByWord,
			key("Control+ExtendedRight"):self.script_text_moveByWord,
			key("Shift+ExtendedRight"):self.script_text_changeSelection,
			key("Shift+ExtendedLeft"):self.script_text_changeSelection,
			key("Shift+ExtendedHome"):self.script_text_changeSelection,
			key("Shift+ExtendedEnd"):self.script_text_changeSelection,
			key("Shift+ExtendedUp"):self.script_text_changeSelection,
			key("Shift+ExtendedDown"):self.script_text_changeSelection,
			key("Control+Shift+ExtendedLeft"):self.script_text_changeSelection,
			key("Control+Shift+ExtendedRight"):self.script_text_changeSelection,
			key("ExtendedHome"):self.script_text_moveByCharacter,
			key("ExtendedEnd"):self.script_text_moveByCharacter,
			key("control+extendedHome"):self.script_text_moveByLine,
			key("control+extendedEnd"):self.script_text_moveByLine,
			key("control+shift+extendedHome"):self.script_text_changeSelection,
			key("control+shift+extendedEnd"):self.script_text_changeSelection,
			key("ExtendedDelete"):self.script_text_delete,
			key("Back"):self.script_text_backspace,
		})

	def _get_name(self):
		name=super(NVDAObject_winEdit,self).name
		if self.text_getText().strip()!=name.strip():
			return name

	def text_getText(self,start=None,end=None):
		start=start if isinstance(start,int) else 0
		end=end if isinstance(end,int) else len(self.value)
		if self.text_lineCount>1:
			startLineNum=self.text_getLineNumber(start)-1
			startOffset=start-self.text_getLineOffsets(start)[0]
			endLineNum=self.text_getLineNumber(end-1)-1
			lines=[]
			for lineNum in xrange(startLineNum,endLineNum+1):
				lineStart=winUser.sendMessage(self.windowHandle,winUser.EM_LINEINDEX,lineNum,0)
				lineLength=winUser.sendMessage(self.windowHandle,winUser.EM_LINELENGTH,lineStart,0)
				buf=ctypes.create_unicode_buffer(lineLength+10)
				buf.value=struct.pack('h',lineLength+2)
				winUser.sendMessage(self.windowHandle,winUser.EM_GETLINE,lineNum,buf)
				lines.append(buf.value[0:lineLength])
			text="".join(lines)
			text=text[startOffset:][:end-start]
			if text=="":
				text='\r'
			return text
		else:
			text=self.windowText
			return text[start:end]

	def _get_text_characterCount(self):
		return winUser.sendMessage(self.windowHandle,winUser.WM_GETTEXTLENGTH,0,0)
 
	def _get_typeString(self):
		typeString=IAccessibleHandler.getRoleName(IAccessibleHandler.ROLE_SYSTEM_TEXT)
		if self.isProtected:
			typeString=_("protected %s ")%typeString
		return typeString

	def _get_value(self):
		r=self.text_getLineOffsets(self.text_caretOffset)
		return self.text_getText(r[0],r[1])

	def _get_text_selectionCount(self):
		long=winUser.sendMessage(self.windowHandle,winUser.EM_GETSEL,0,0)
		start=winUser.LOWORD(long)
		end=winUser.HIWORD(long)
		if start!=end:
			return 1
		else:
			return 0

	def text_getSelectionOffsets(self,index):
		if index!=0:
			return None
		long=winUser.sendMessage(self.windowHandle,winUser.EM_GETSEL,0,0)
		start=winUser.LOWORD(long)
		end=winUser.HIWORD(long)
		if start!=end:
			return (start,end)
		else:
			return None

	def _get_text_caretOffset(self):
		long=winUser.sendMessage(self.windowHandle,winUser.EM_GETSEL,0,0)
		pos=winUser.LOWORD(long)
		return pos

	def _set_text_caretOffset(self,pos):
		winUser.sendMessage(self.windowHandle,winUser.EM_SETSEL,pos,pos)

	def text_getLineNumber(self,offset):
		return winUser.sendMessage(self.windowHandle,winUser.EM_LINEFROMCHAR,offset,0)+1

	def _get_text_lineCount(self):
		return winUser.sendMessage(self.windowHandle,winUser.EM_GETLINECOUNT,0,0)

	def text_getLineOffsets(self,offset):
		if self.text_lineCount<1:
			return (0,self.text_characterCount)
		lineNum=self.text_getLineNumber(offset)-1
		lineStart=winUser.sendMessage(self.windowHandle,winUser.EM_LINEINDEX,lineNum,0)
		lineLength=winUser.sendMessage(self.windowHandle,winUser.EM_LINELENGTH,lineStart,0)
		lineEnd=lineStart+lineLength
		return (lineStart,lineEnd)

	def text_getNextLineOffsets(self,offset):
		(start,end)=self.text_getLineOffsets(offset)
		startLineNum=self.text_getLineNumber(start)
		if self.text_getLineNumber(end)!=startLineNum:
			return self.text_getLineOffsets(end)
		limit=self.text_characterCount
		while end<limit:
			end+=1
			if self.text_getLineNumber(end)!=startLineNum:
				return self.text_getLineOffsets(end)
		return None


	def event_valueChange(self):
		pass


