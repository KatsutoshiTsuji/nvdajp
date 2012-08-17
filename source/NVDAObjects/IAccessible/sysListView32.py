# -*- coding: UTF-8 -*-
#NVDAObjects/IAccessible/sysListView32.py
#A part of NonVisual Desktop Access (NVDA)
#Copyright (C) 2006-2012 NV Access Limited, Peter V�gner
#This file is covered by the GNU General Public License.
#See the file COPYING for more details.

import time
from ctypes import *
from ctypes.wintypes import *
import oleacc
import controlTypes
import speech
import api
import eventHandler
import winKernel
import winUser
from . import IAccessible, List
from ..window import Window
import watchdog
from NVDAObjects.behaviors import RowWithoutCellObjects, RowWithFakeNavigation

#Window messages
LVM_FIRST=0x1000
LVM_GETITEMSTATE=LVM_FIRST+44
LVM_GETFOCUSEDGROUP=LVM_FIRST+93
LVM_GETGROUPINFOBYINDEX=LVM_FIRST+153
LVM_GETITEMCOUNT=LVM_FIRST+4
LVM_GETITEM=LVM_FIRST+75
LVN_GETDISPINFO=0xFFFFFF4F
LVM_GETITEMTEXTW=LVM_FIRST+115
LVM_GETHEADER=LVM_FIRST+31
LVM_GETCOLUMNORDERARRAY=LVM_FIRST+59
LVM_GETCOLUMNW=LVM_FIRST+95
LVM_GETSELECTEDCOUNT =(LVM_FIRST+50)
LVNI_SELECTED =2
LVM_GETNEXTITEM =(LVM_FIRST+12)

#item mask flags
LVIF_TEXT=0x01 
LVIF_IMAGE=0x02
LVIF_PARAM=0x04
LVIF_STATE=0x08
LVIF_INDENT=0x10
LVIF_GROUPID=0x100
LVIF_COLUMNS=0x200

#group mask flags
LVGF_HEADER=0x1
LVGF_FOOTER=0x2
LVGF_STATE=0x4
LVGF_ALIGN=0x8
LVGF_GROUPID=0x10

#Item states
LVIS_FOCUSED=0x01
LVIS_SELECTED=0x02
LVIS_STATEIMAGEMASK=0xF000

LVS_REPORT=0x0001
LVS_OWNERDRAWFIXED=0x0400

#column mask flags
LVCF_FMT=1
LVCF_WIDTH=2
LVCF_TEXT=4
LVCF_SUBITEM=8
LVCF_IMAGE=16
LVCF_ORDER=32

CBEMAXSTRLEN=260

# listview header window messages
HDM_FIRST=0x1200
HDM_GETITEMCOUNT=HDM_FIRST

class LVGROUP(Structure):
	_fields_=[
		('cbSize',c_uint),
		('mask',c_uint),
		('pszHeader',c_void_p),
		('cchHeader',c_int),
		('pszFooter',c_void_p),
		('cchFooter',c_int),
		('iGroupId',c_int),
		('stateMask',c_uint),
		('state',c_uint),
		('uAlign',c_uint),
		('pszSubtitle',c_void_p),
		('cchSubtitle',c_uint),
		('pszTask',c_void_p),
		('cchTask',c_uint),
		('pszDescriptionTop',c_void_p),
		('cchDescriptionTop',c_uint),
		('pszDescriptionBottom',c_void_p),
		('cchDescriptionBottom',c_uint),
		('iTitleImage',c_int),
		('iExtendedImage',c_int),
		('iFirstItem',c_int),
		('cItems',c_uint),
		('pszSubsetTitle',c_void_p),
		('cchSubsetTitle',c_uint),
	]

class LVITEM(Structure):
	_fields_=[
		('mask',c_uint),
		('iItem',c_int),
		('iSubItem',c_int),
		('state',c_uint),
		('stateMask',c_uint),
		('pszText',c_void_p),
		('cchTextMax',c_int),
		('iImage',c_int),
		('lParam',LPARAM),
		('iIndent',c_int),
		('iGroupID',c_int),
		('cColumns',c_uint),
		('puColumns',c_uint),
		('piColFmt',POINTER(c_int)),
		('iGroup',c_int),
	]

class LVITEM64(Structure):
	_fields_=[
		('mask',c_uint),
		('iItem',c_int),
		('iSubItem',c_int),
		('state',c_uint),
		('stateMask',c_uint),
		('pszText',c_longlong),
		('cchTextMax',c_int),
		('iImage',c_int),
		('lParam',c_longlong),
		('iIndent',c_int),
		('iGroupID',c_int),
		('cColumns',c_uint),
		('puColumns',c_uint),
		('piColFmt',c_longlong),
		('iGroup',c_int),
	]

class NMLVDispInfoStruct(Structure):
	_fields_=[
		('hdr',winUser.NMHdrStruct),
		('item',c_int),
	]

class LVCOLUMN(Structure):
	_fields_=[
		('mask',c_uint),
		('fmt',c_int),
		('cx',c_int),
		('pszText',c_void_p),
		('cchTextMax',c_int),
		('iSubItem',c_int),
		('iImage',c_int),
		('iOrder',c_int),
		('cxMin',c_int),
		('cxDefault',c_int),
		('cxIdeal',c_int),
	]

class LVCOLUMN64(Structure):
	_fields_=[
		('mask',c_uint),
		('fmt',c_int),
		('cx',c_int),
		('pszText',c_longlong),
		('cchTextMax',c_int),
		('iSubItem',c_int),
		('iImage',c_int),
		('iOrder',c_int),
		('cxMin',c_int),
		('cxDefault',c_int),
		('cxIdeal',c_int),
	]

def getListGroupInfo(windowHandle,groupIndex):
	processHandle=oleacc.GetProcessHandleFromHwnd(windowHandle)
	if not processHandle:
		return None
	localInfo=LVGROUP()
	localInfo.cbSize=sizeof(LVGROUP)
	localInfo.mask=LVGF_HEADER|LVGF_FOOTER|LVGF_STATE|LVGF_ALIGN|LVGF_GROUPID
	localInfo.stateMask=0xffffffff
	remoteInfo=winKernel.virtualAllocEx(processHandle,None,sizeof(LVGROUP),winKernel.MEM_COMMIT,winKernel.PAGE_READWRITE)
	try:
		winKernel.writeProcessMemory(processHandle,remoteInfo,byref(localInfo),sizeof(LVGROUP),None)
		messageRes=watchdog.cancellableSendMessage(windowHandle,LVM_GETGROUPINFOBYINDEX,groupIndex,remoteInfo)
		winKernel.readProcessMemory(processHandle,remoteInfo,byref(localInfo),sizeof(LVGROUP),None)
	finally:
		winKernel.virtualFreeEx(processHandle,remoteInfo,0,winKernel.MEM_RELEASE)
	localHeader=create_unicode_buffer(localInfo.cchHeader)
	winKernel.readProcessMemory(processHandle,localInfo.pszHeader,localHeader,localInfo.cchHeader*2,None)
	localFooter=create_unicode_buffer(localInfo.cchFooter)
	winKernel.readProcessMemory(processHandle,localInfo.pszFooter,localFooter,localInfo.cchFooter*2,None)
	winKernel.closeHandle(processHandle)
	if messageRes==1:
		return dict(header=localHeader.value,footer=localFooter.value,groupID=localInfo.iGroupId,state=localInfo.state,uAlign=localInfo.uAlign,groupIndex=groupIndex)
	else:
		return None

class List(List):

	def _get_name(self):
		name=super(List,self)._get_name()
		if not name:
			name=super(IAccessible,self)._get_name()
		return name

	def event_gainFocus(self):
		#See if this object is the focus and the focus is on a group item.
		#if so, then morph this object to a groupingItem object
		if self is api.getFocusObject():
			groupIndex=watchdog.cancellableSendMessage(self.windowHandle,LVM_GETFOCUSEDGROUP,0,0)
			if groupIndex>=0:
				info=getListGroupInfo(self.windowHandle,groupIndex)
				if info is not None:
					ancestors=api.getFocusAncestors()
					if api.getFocusDifferenceLevel()==len(ancestors)-1:
						self.event_focusEntered()
					groupingObj=GroupingItem(windowHandle=self.windowHandle,parentNVDAObject=self,groupInfo=info)
					return eventHandler.queueEvent("gainFocus",groupingObj)
		return super(List,self).event_gainFocus()

	def _get_rowCount(self):
		return watchdog.cancellableSendMessage(self.windowHandle, LVM_GETITEMCOUNT, 0, 0)

	def _get_columnCount(self):
		if not (self.windowStyle & LVS_REPORT):
			return 0
		headerHwnd= watchdog.cancellableSendMessage(self.windowHandle,LVM_GETHEADER,0,0)
		count = watchdog.cancellableSendMessage(headerHwnd, HDM_GETITEMCOUNT, 0, 0)
		if not count:
			return 1
		return count

	def _get__columnOrderArray(self):
		coa=(c_int *self.columnCount)()
		processHandle=self.processHandle
		internalCoa=winKernel.virtualAllocEx(processHandle,None,sizeof(coa),winKernel.MEM_COMMIT,winKernel.PAGE_READWRITE)
		try:
			winKernel.writeProcessMemory(processHandle,internalCoa,byref(coa),sizeof(coa),None)
			res = watchdog.cancellableSendMessage(self.windowHandle,LVM_GETCOLUMNORDERARRAY, self.columnCount, internalCoa)
			if res:
				winKernel.readProcessMemory(processHandle,internalCoa,byref(coa),sizeof(coa),None)
		finally:
			winKernel.virtualFreeEx(processHandle,internalCoa,0,winKernel.MEM_RELEASE)
		return coa

class GroupingItem(Window):

	def __init__(self,windowHandle=None,parentNVDAObject=None,groupInfo=None):
		super(GroupingItem,self).__init__(windowHandle=windowHandle)
		self.parent=parentNVDAObject
		self.groupInfo=groupInfo

	def _isEqual(self,other):
		return isinstance(other,self.__class__) and self.groupInfo==other.groupInfo

	def _set_groupInfo(self,info):
		self._groupInfoTime=time.time()
		self._groupInfo=info

	def _get_groupInfo(self):
		now=time.time()
		if (now-self._groupInfoTime)>0.25:
			self._groupInfoTime=now
			self._groupInfo=getListGroupInfo(self.windowHandle,self._groupInfo['groupIndex'])
		return self._groupInfo

	def _get_name(self):
		return self.groupInfo['header']

	def _get_role(self):
		return controlTypes.ROLE_GROUPING

	def _get_value(self):
		return self.groupInfo['footer']

	def _get_states(self):
		states=set()
		if self.groupInfo['state']&1:
			states.add(controlTypes.STATE_COLLAPSED)
		else:
			states.add(controlTypes.STATE_EXPANDED)
		return states

	def script_collapseOrExpand(self,gesture):
		gesture.send()
		self.event_stateChange()

	def initOverlayClass(self):
		for gesture in ("kb:leftArrow", "kb:rightArrow"):
			self.bindGesture(gesture, "collapseOrExpand")

class ListItem(IAccessible):

	def initOverlayClass(self):
		if self.appModule.is64BitProcess:
			self.LVITEM = LVITEM64
			self.LVCOLUMN = LVCOLUMN64
		else:
			self.LVITEM = LVITEM
			self.LVCOLUMN = LVCOLUMN

	def _get_lvAppImageID(self):
		item=self.LVITEM(iItem=self.IAccessibleChildID-1,mask=LVIF_IMAGE)
		processHandle=self.processHandle
		internalItem=winKernel.virtualAllocEx(processHandle,None,sizeof(self.LVITEM),winKernel.MEM_COMMIT,winKernel.PAGE_READWRITE)
		try:
			winKernel.writeProcessMemory(processHandle,internalItem,byref(item),sizeof(self.LVITEM),None)
			watchdog.cancellableSendMessage(self.windowHandle,LVM_GETITEM,0,internalItem)
			dispInfo=NMLVDispInfoStruct()
			dispInfo.item=internalItem
			dispInfo.hdr.hwndFrom=self.windowHandle
			dispInfo.hdr.idFrom=self.windowControlID
			dispInfo.hdr.code=LVN_GETDISPINFO
			internalDispInfo=winKernel.virtualAllocEx(processHandle,None,sizeof(NMLVDispInfoStruct),winKernel.MEM_COMMIT,winKernel.PAGE_READWRITE)
			try:
				winKernel.writeProcessMemory(processHandle,internalDispInfo,byref(dispInfo),sizeof(NMLVDispInfoStruct),None)
				watchdog.cancellableSendMessage(self.parent.parent.windowHandle,winUser.WM_NOTIFY,LVN_GETDISPINFO,internalDispInfo)
			finally:
				winKernel.virtualFreeEx(processHandle,internalDispInfo,0,winKernel.MEM_RELEASE)
			winKernel.readProcessMemory(processHandle,internalItem,byref(item),sizeof(self.LVITEM),None)
		finally:
			winKernel.virtualFreeEx(processHandle,internalItem,0,winKernel.MEM_RELEASE)
		return item.iImage

	def _get_description(self):
		return None

	def _get_value(self):
		value=super(ListItem,self)._get_description()
		if (not value or value.isspace()) and self.windowStyle & LVS_OWNERDRAWFIXED:
			value=self.displayText
		if not value:
			return None
		#Some list view items in Vista can contain annoying left-to-right and right-to-left indicator characters which really should not be there.
		value=value.replace(u'\u200E','')
		value=value.replace(u'\u200F','')
		return value

	def _get_positionInfo(self):
		index=self.IAccessibleChildID
		totalCount=watchdog.cancellableSendMessage(self.windowHandle,LVM_GETITEMCOUNT,0,0)
		return dict(indexInGroup=index,similarItemsInGroup=totalCount) 

	def event_stateChange(self):
		if self.hasFocus:
			super(ListItem,self).event_stateChange()

class ListItemWithReportView(RowWithFakeNavigation, RowWithoutCellObjects, ListItem):

	def _getColumnContentRaw(self, index):
		buffer=None
		processHandle=self.processHandle
		internalItem=winKernel.virtualAllocEx(processHandle,None,sizeof(self.LVITEM),winKernel.MEM_COMMIT,winKernel.PAGE_READWRITE)
		try:
			internalText=winKernel.virtualAllocEx(processHandle,None,CBEMAXSTRLEN*2,winKernel.MEM_COMMIT,winKernel.PAGE_READWRITE)
			try:
				item=self.LVITEM(iItem=self.IAccessibleChildID-1,mask=LVIF_TEXT|LVIF_COLUMNS,iSubItem=index,pszText=internalText,cchTextMax=CBEMAXSTRLEN)
				winKernel.writeProcessMemory(processHandle,internalItem,byref(item),sizeof(self.LVITEM),None)
				len = watchdog.cancellableSendMessage(self.windowHandle,LVM_GETITEMTEXTW, (self.IAccessibleChildID-1), internalItem)
				if len:
					winKernel.readProcessMemory(processHandle,internalItem,byref(item),sizeof(self.LVITEM),None)
					buffer=create_unicode_buffer(len)
					winKernel.readProcessMemory(processHandle,item.pszText,buffer,sizeof(buffer),None)
			finally:
				winKernel.virtualFreeEx(processHandle,internalText,0,winKernel.MEM_RELEASE)
		finally:
			winKernel.virtualFreeEx(processHandle,internalItem,0,winKernel.MEM_RELEASE)
		return buffer.value if buffer else None

	def _getColumnContent(self, column):
		return self._getColumnContentRaw(self.parent._columnOrderArray[column - 1])

	def _getColumnHeaderRaw(self,index):
		buffer=None
		processHandle=self.processHandle
		internalColumn=winKernel.virtualAllocEx(processHandle,None,sizeof(self.LVCOLUMN),winKernel.MEM_COMMIT,winKernel.PAGE_READWRITE)
		try:
			internalText=winKernel.virtualAllocEx(processHandle,None,CBEMAXSTRLEN*2,winKernel.MEM_COMMIT,winKernel.PAGE_READWRITE)
			try:
				column=self.LVCOLUMN(mask=LVCF_TEXT,iSubItem=index,pszText=internalText,cchTextMax=CBEMAXSTRLEN)
				winKernel.writeProcessMemory(processHandle,internalColumn,byref(column),sizeof(self.LVCOLUMN),None)
				res = watchdog.cancellableSendMessage(self.windowHandle,LVM_GETCOLUMNW, index, internalColumn)
				if res:
					winKernel.readProcessMemory(processHandle,internalColumn,byref(column),sizeof(self.LVCOLUMN),None)
					buffer=create_unicode_buffer(column.cchTextMax)
					winKernel.readProcessMemory(processHandle,column.pszText,buffer,sizeof(buffer),None)
			finally:
				winKernel.virtualFreeEx(processHandle,internalText,0,winKernel.MEM_RELEASE)
		finally:
			winKernel.virtualFreeEx(processHandle,internalColumn,0,winKernel.MEM_RELEASE)
		return buffer.value if buffer else None

	def _getColumnHeader(self, column):
		return self._getColumnHeaderRaw(self.parent._columnOrderArray[column - 1])

	def _get_name(self):
		if not (self.windowStyle & LVS_REPORT):
			return super(ListItemWithReportView, self).name
		textList = []
		for col in xrange(1, self.childCount + 1):
			text = self._getColumnContent(col)
			if not text:
				continue
			textList.append(text)
		return "; ".join(textList)

	value = None
