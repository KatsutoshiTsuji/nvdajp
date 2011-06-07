from ctypes import *
from ctypes.wintypes import *
import comtypes.client
from comtypes import *
import weakref
import threading
import time
import api
import queueHandler
import controlTypes
import winKernel
import winUser
import eventHandler
from logHandler import log

from comtypes.gen.UIAutomationClient import *

badUIAWindowClassNames=[
	"SysTreeView32",
	"WuDuiListView",
	"ComboBox",
	"msctls_progress32",
	"Edit",
	"CommonPlacesWrapperWndClass",
]

UIAControlTypesToNVDARoles={
	UIA_ButtonControlTypeId:controlTypes.ROLE_BUTTON,
	UIA_CalendarControlTypeId:controlTypes.ROLE_CALENDAR,
	UIA_CheckBoxControlTypeId:controlTypes.ROLE_CHECKBOX,
	UIA_ComboBoxControlTypeId:controlTypes.ROLE_COMBOBOX,
	UIA_EditControlTypeId:controlTypes.ROLE_EDITABLETEXT,
	UIA_HyperlinkControlTypeId:controlTypes.ROLE_LINK,
	UIA_ImageControlTypeId:controlTypes.ROLE_GRAPHIC,
	UIA_ListItemControlTypeId:controlTypes.ROLE_LISTITEM,
	UIA_ListControlTypeId:controlTypes.ROLE_LIST,
	UIA_MenuControlTypeId:controlTypes.ROLE_POPUPMENU,
	UIA_MenuBarControlTypeId:controlTypes.ROLE_MENUBAR,
	UIA_MenuItemControlTypeId:controlTypes.ROLE_MENUITEM,
	UIA_ProgressBarControlTypeId:controlTypes.ROLE_PROGRESSBAR,
	UIA_RadioButtonControlTypeId:controlTypes.ROLE_RADIOBUTTON,
	UIA_ScrollBarControlTypeId:controlTypes.ROLE_SCROLLBAR,
	UIA_SliderControlTypeId:controlTypes.ROLE_SLIDER,
	UIA_SpinnerControlTypeId:controlTypes.ROLE_SPINBUTTON,
	UIA_StatusBarControlTypeId:controlTypes.ROLE_STATUSBAR,
	UIA_TabControlTypeId:controlTypes.ROLE_TABCONTROL,
	UIA_TabItemControlTypeId:controlTypes.ROLE_TAB,
	UIA_TextControlTypeId:controlTypes.ROLE_STATICTEXT,
	UIA_ToolBarControlTypeId:controlTypes.ROLE_TOOLBAR,
	UIA_ToolTipControlTypeId:controlTypes.ROLE_TOOLTIP,
	UIA_TreeControlTypeId:controlTypes.ROLE_TREEVIEW,
	UIA_TreeItemControlTypeId:controlTypes.ROLE_TREEVIEWITEM,
	UIA_CustomControlTypeId:controlTypes.ROLE_UNKNOWN,
	UIA_GroupControlTypeId:controlTypes.ROLE_GROUPING,
	UIA_ThumbControlTypeId:controlTypes.ROLE_THUMB,
	UIA_DataGridControlTypeId:controlTypes.ROLE_DATAGRID,
	UIA_DataItemControlTypeId:controlTypes.ROLE_DATAITEM,
	UIA_DocumentControlTypeId:controlTypes.ROLE_DOCUMENT,
	UIA_SplitButtonControlTypeId:controlTypes.ROLE_SPLITBUTTON,
	UIA_WindowControlTypeId:controlTypes.ROLE_WINDOW,
	UIA_PaneControlTypeId:controlTypes.ROLE_PANE,
	UIA_HeaderControlTypeId:controlTypes.ROLE_HEADER,
	UIA_HeaderItemControlTypeId:controlTypes.ROLE_HEADERITEM,
	UIA_TableControlTypeId:controlTypes.ROLE_TABLE,
	UIA_TitleBarControlTypeId:controlTypes.ROLE_TITLEBAR,
	UIA_SeparatorControlTypeId:controlTypes.ROLE_SEPARATOR,
}

UIAPropertyIdsToNVDAEventNames={
	UIA_NamePropertyId:"nameChange",
	UIA_HelpTextPropertyId:"descriptionChange",
	UIA_ExpandCollapseExpandCollapseStatePropertyId:"stateChange",
	UIA_ToggleToggleStatePropertyId:"stateChange",
	UIA_IsEnabledPropertyId:"stateChange",
	UIA_ValueValuePropertyId:"valueChange",
	UIA_RangeValueValuePropertyId:"valueChange",
}

UIAEventIdsToNVDAEventNames={
	#UIA_Text_TextChangedEventId:"textChanged",
	UIA_SelectionItem_ElementSelectedEventId:"stateChange",
	#UIA_MenuOpenedEventId:"gainFocus",
	UIA_SelectionItem_ElementAddedToSelectionEventId:"stateChange",
	UIA_SelectionItem_ElementRemovedFromSelectionEventId:"stateChange",
	#UIA_MenuModeEndEventId:"menuModeEnd",
	#UIA_Text_TextSelectionChangedEventId:"caret",
	#UIA_ToolTipOpenedEventId:"show",
	#UIA_AsyncContentLoadedEventId:"documentLoadComplete",
	#UIA_ToolTipClosedEventId:"hide",
}

class UIAHandler(COMObject):
	_com_interfaces_=[IUIAutomationEventHandler,IUIAutomationFocusChangedEventHandler,IUIAutomationPropertyChangedEventHandler]

	def __init__(self):
		super(UIAHandler,self).__init__()
		self.MTAThreadInitEvent=threading.Event()
		self.MTAThreadStopEvent=threading.Event()
		self.MTAThreadInitException=None
		self.MTAThread=threading.Thread(target=self.MTAThreadFunc)
		self.MTAThread.start()
		self.MTAThreadInitEvent.wait(2)
		if self.MTAThreadInitException:
			raise self.MTAThreadInitException

	def terminate(self):
		MTAThreadHandle=HANDLE(windll.kernel32.OpenThread(self.MTAThread.ident,False,winKernel.SYNCHRONIZE))
		self.MTAThreadStopEvent.set()
		index=c_int()
		#Wait for the MTAA thread to die (while still message pumping)
		windll.user32.MsgWaitForMultipleObjects(1,byref(MTAThreadHandle),False,5000,0)
		del self.MTAThread

	def MTAThreadFunc(self):
		try:
			oledll.ole32.CoInitializeEx(None,comtypes.COINIT_MULTITHREADED) 
			self.clientObject=CoCreateInstance(CUIAutomation._reg_clsid_,interface=IUIAutomation,clsctx=CLSCTX_INPROC_SERVER)
			self.windowTreeWalker=self.clientObject.createTreeWalker(self.clientObject.CreateNotCondition(self.clientObject.CreatePropertyCondition(UIA_NativeWindowHandlePropertyId,0)))
			self.windowCacheRequest=self.clientObject.CreateCacheRequest()
			self.windowCacheRequest.AddProperty(UIA_NativeWindowHandlePropertyId)
			self.UIAWindowHandleCache={}
			self.baseTreeWalker=self.clientObject.RawViewWalker
			self.baseCacheRequest=self.windowCacheRequest.Clone()
			for propertyId in (UIA_ClassNamePropertyId,UIA_ControlTypePropertyId,UIA_IsKeyboardFocusablePropertyId,UIA_IsPasswordPropertyId,UIA_ProviderDescriptionPropertyId,UIA_ProcessIdPropertyId,UIA_IsSelectionItemPatternAvailablePropertyId,UIA_IsTextPatternAvailablePropertyId):
				self.baseCacheRequest.addProperty(propertyId)
			self.rootElement=self.clientObject.getRootElementBuildCache(self.baseCacheRequest)
			self.reservedNotSupportedValue=self.clientObject.ReservedNotSupportedValue
			self.clientObject.AddFocusChangedEventHandler(self.baseCacheRequest,self)
			self.clientObject.AddPropertyChangedEventHandler(self.rootElement,TreeScope_Subtree,self.baseCacheRequest,self,UIAPropertyIdsToNVDAEventNames.keys())
			for x in UIAEventIdsToNVDAEventNames.iterkeys():  
				self.clientObject.addAutomationEventHandler(x,self.rootElement,TreeScope_Subtree,self.baseCacheRequest,self)
		except Exception as e:
			self.MTAThreadInitException=e
		finally:
			self.MTAThreadInitEvent.set()
		self.MTAThreadStopEvent.wait()
		self.clientObject.RemoveAllEventHandlers()

	def IUIAutomationEventHandler_HandleAutomationEvent(self,sender,eventID):
		if not self.MTAThreadInitEvent.isSet:
			# UIAHandler hasn't finished initialising yet, so just ignore this event.
			return
		NVDAEventName=UIAEventIdsToNVDAEventNames.get(eventID,None)
		if not NVDAEventName:
			return
		if not self.isNativeUIAElement(sender):
			return
		import NVDAObjects.UIA
		obj=NVDAObjects.UIA.UIA(UIAElement=sender)
		if not obj:
			return
		eventHandler.queueEvent(NVDAEventName,obj)

	def IUIAutomationFocusChangedEventHandler_HandleFocusChangedEvent(self,sender):
		if not self.MTAThreadInitEvent.isSet:
			# UIAHandler hasn't finished initialising yet, so just ignore this event.
			return
		if not self.isNativeUIAElement(sender):
			return
		try:
			hasFocus=sender.currentHasKeyboardFocus
		except COMError:
			return
		if not hasFocus: 
			return
		import NVDAObjects.UIA
		if isinstance(eventHandler.lastQueuedFocusObject,NVDAObjects.UIA.UIA):
			lastFocus=eventHandler.lastQueuedFocusObject.UIAElement
			# Ignore duplicate focus events.
			# It seems that it is possible for compareElements to return True, even though the objects are different.
			# Therefore, don't ignore the event if the last focus object has lost its hasKeyboardFocus state.
			if self.clientObject.compareElements(sender,lastFocus) and lastFocus.currentHasKeyboardFocus:
				return
		obj=NVDAObjects.UIA.UIA(UIAElement=sender)
		eventHandler.queueEvent("gainFocus",obj)

	def IUIAutomationPropertyChangedEventHandler_HandlePropertyChangedEvent(self,sender,propertyId,newValue):
		if not self.MTAThreadInitEvent.isSet:
			# UIAHandler hasn't finished initialising yet, so just ignore this event.
			return
		NVDAEventName=UIAPropertyIdsToNVDAEventNames.get(propertyId,None)
		if not NVDAEventName:
			return
		if not self.isNativeUIAElement(sender):
			return
		import NVDAObjects.UIA
		obj=NVDAObjects.UIA.UIA(UIAElement=sender)
		if not obj:
			return
		eventHandler.queueEvent(NVDAEventName,obj)

	def isUIAWindow(self,hwnd):
		now=time.time()
		v=self.UIAWindowHandleCache.get(hwnd,None)
		if not v or (now-v[1])>0.5:
			if windll.kernel32.GetCurrentProcessId()==winUser.getWindowThreadProcessID(hwnd)[0]:
				isUIA=False
			elif winUser.getClassName(hwnd) in badUIAWindowClassNames:
				isUIA=False
			else:
				isUIA=windll.UIAutomationCore.UiaHasServerSideProvider(hwnd)
			self.UIAWindowHandleCache[hwnd]=(isUIA,now)
			return isUIA
		return v[0]

	def getNearestWindowHandle(self,UIAElement):
		try:
			UIAElement=self.windowTreeWalker.NormalizeElementBuildCache(UIAElement,self.windowCacheRequest)
		except COMError:
			return None
		try:
			return UIAElement.cachedNativeWindowHandle
		except COMError:
			return None

	def isNativeUIAElement(self,UIAElement):
		#Due to issues dealing with UIA elements coming from the same process, we do not class these UIA elements as usable.
		#It seems to be safe enough to retreave the cached processID, but using tree walkers or fetching other properties causes a freeze.
		try:
			processID=UIAElement.cachedProcessId
		except COMError:
			return False
		if processID==windll.kernel32.GetCurrentProcessId():
			return False
		#If the element has a window handle, and the window natively supports UIA, then its a native element
		try:
			windowHandle=UIAElement.cachedNativeWindowHandle
		except COMError:
			windowHandle=None
		if windowHandle:
			return self.isUIAWindow(windowHandle)
		#The element does not have a window, but we can class it as native if the element is not an MSAA proxy (according to provider description)
		try:
			providerDescription=UIAElement.cachedProviderDescription
		except COMError:
			return True
		return "Microsoft: MSAA Proxy (unmanaged:uiautomationcore.dll)" not in providerDescription

