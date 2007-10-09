#appModules/miranda32.py
#A part of NonVisual Desktop Access (NVDA)
#Copyright (C) 2006-2007 NVDA Contributors <http://www.nvda-project.org/>
#This file is covered by the GNU General Public License.
#See the file COPYING for more details.

from ctypes import *
from ctypes.wintypes import *
import winKernel
import winUser
from NVDAObjects.IAccessible import IAccessible, IAccessibleStatesToNVDAStates
import appModuleHandler
import speech
import debug
import controlTypes
from keyUtils import sendKey, isKeyWaiting
import api
import IAccessibleHandler

#contact list window messages
CLM_FIRST=0x1000    #this is the same as LVM_FIRST
CLM_LAST=0x1100

#messages, compare with equivalent TVM_s in the MSDN
CLM_ENSUREVISIBLE=(CLM_FIRST+6)    #wParam=hItem, lParam=partialOk
CLE_TOGGLE=-1
CLE_COLLAPSE=0
CLE_EXPAND=1
CLE_INVALID=0xFFFF
CLM_EXPAND=(CLM_FIRST+7)    #wParam=hItem, lParam=CLE_
CLM_FINDCONTACT=(CLM_FIRST+8)    #wParam=hContact, returns an hItem
CLM_FINDGROUP=(CLM_FIRST+9)    #wParam=hGroup, returns an hItem
CLM_GETBKCOLOR=(CLM_FIRST+10)   #returns a COLORREF
CLM_GETCHECKMARK=(CLM_FIRST+11)   #wParam=hItem, returns 1 or 0
CLM_GETCOUNT=(CLM_FIRST+12)   #returns the total number of items
CLM_GETEXPAND=(CLM_FIRST+14)   #wParam=hItem, returns a CLE_, CLE_INVALID if not a group
CLM_GETEXTRACOLUMNS=(CLM_FIRST+15)   #returns number of extra columns
CLM_GETEXTRAIMAGE=(CLM_FIRST+16)   #wParam=hItem, lParam=MAKELPARAM(iColumn (0 based),0), returns iImage or 0xFF
CLM_GETEXTRAIMAGELIST=(CLM_FIRST+17)   #returns HIMAGELIST
CLM_GETFONT=(CLM_FIRST+18)   #wParam=fontId, see clm_setfont. returns hFont.
CLM_GETINDENT=(CLM_FIRST+19)   #wParam=new group indent
CLM_GETISEARCHSTRING=(CLM_FIRST+20)   #lParam=(char*)pszStr, max 120 bytes, returns number of chars in string
CLM_GETITEMTEXT=CLM_FIRST+21   #wParam=hItem, lParam=(char*)pszStr, max 120 bytes
CLM_GETSELECTION=(CLM_FIRST+23)   #returns hItem
CLM_SELECTITEM=(CLM_FIRST+26)   #wParam=hItem
CLM_GETHIDEOFFLINEROOT=(CLM_FIRST+40)   #returns TRUE/FALSE
CLM_GETEXSTYLE=(CLM_FIRST+44)   #returns CLS_EX_ flags
CLM_GETLEFTMARGIN=(CLM_FIRST+46)   #returns count of pixels
CLCIT_INVALID=-1
CLCIT_GROUP=0
CLCIT_CONTACT=1
CLCIT_DIVIDER=2
CLCIT_INFO=3
CLM_GETITEMTYPE=(CLM_FIRST+49)	#wParam=hItem, returns a CLCIT_
CLGN_ROOT=0
CLGN_CHILD=1
CLGN_PARENT=2
CLGN_NEXT=3
CLGN_PREVIOUS=4
CLGN_NEXTCONTACT=5
CLGN_PREVIOUSCONTACT=6
CLGN_NEXTGROUP=7
CLGN_PREVIOUSGROUP=8
CLM_GETNEXTITEM=(CLM_FIRST+50)   #wParam=flag, lParam=hItem, returns an hItem
CLM_GETTEXTCOLOR=(CLM_FIRST+51)   #wParam=FONTID_, returns COLORREF

class appModule(appModuleHandler.appModule):

	def event_NVDAObject_init(self,obj):
		if obj.windowClassName=="CListControl":
			obj.__class__=mirandaIMContactList

class mirandaIMContactList(IAccessible):

	def _get_name(self):
		hItem=winUser.sendMessage(self.windowHandle,CLM_GETSELECTION,0,0)
		processHandle=winKernel.openProcess(winKernel.PROCESS_VM_OPERATION|winKernel.PROCESS_VM_READ|winKernel.PROCESS_VM_WRITE,False,self.windowProcessID)
		internalBuf=winKernel.virtualAllocEx(processHandle,None,120,winKernel.MEM_COMMIT,winKernel.PAGE_READWRITE)
		winUser.sendMessage(self.windowHandle,CLM_GETITEMTEXT,hItem,internalBuf)
		buf=create_unicode_buffer(120)
		winKernel.readProcessMemory(processHandle,internalBuf,buf,120,None)
		winKernel.virtualFreeEx(processHandle,internalBuf,0,winKernel.MEM_RELEASE)
#		debug.writeMessage("contact: %s from handle: %d"%(buf.value,hItem))
		return buf.value

	def _get_role(self):
		hItem=winUser.sendMessage(self.windowHandle,CLM_GETSELECTION,0,0)
		iType=winUser.sendMessage(self.windowHandle,CLM_GETITEMTYPE,hItem,0)
#		debug.writeMessage("contact type: %d"%iType)
		if iType==CLCIT_DIVIDER|iType==CLCIT_INVALID: #some clists treat invalid as divider
			return controlTypes.ROLE_SEPARATOR
		else:
			return controlTypes.ROLE_TREEVIEWITEM

	def _get_states(self):
		newStates=[]
		for state in api.createStateList(self.IAccessibleStates):
			if IAccessibleStatesToNVDAStates.has_key(state):
				newStates.append(IAccessibleStatesToNVDAStates[state])
		hItem=winUser.sendMessage(self.windowHandle,CLM_GETSELECTION,0,0)
		state=winUser.sendMessage(self.windowHandle,CLM_GETEXPAND,hItem,0)
		if state==CLE_EXPAND:
			newStates.append(controlTypes.STATE_EXPANDED)
		elif state==CLE_COLLAPSE:
			newStates.append(controlTypes.STATE_COLLAPSED)
		return frozenset(newStates)

	def script_changeItem(self,keyPress,nextScript):
		sendKey(keyPress)
		if not isKeyWaiting():
			api.processPendingEvents()
			speech.speakObject(self,reason=speech.REASON_FOCUS)

[mirandaIMContactList.bindKey(keyName,scriptName) for keyName,scriptName in [
	("extendedDown","changeItem"),
	("extendedUp","changeItem"),
	("extendedLeft","changeItem"),
	("extendedRight","changeItem"),
	("extendedHome","changeItem"),
	("extendedEnd","changeItem"),
	("extendedPrior","changeItem"),
	("extendedNext","changeItem"),
]]
