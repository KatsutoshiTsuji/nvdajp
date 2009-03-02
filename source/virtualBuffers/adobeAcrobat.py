import time
import ctypes
from . import VirtualBuffer, VirtualBufferTextInfo
import virtualBufferHandler
import controlTypes
import NVDAObjects.IAccessible
import winUser
import sayAllHandler
import speech
import eventHandler
import IAccessibleHandler
import globalVars
from logHandler import log
import api
import textHandler

class AdobeAcrobat_TextInfo(VirtualBufferTextInfo):

	def _normalizeControlField(self,attrs):
		accRole=attrs['iaccessible::role']
		if accRole.isdigit():
			accRole=int(accRole)
		else:
			accRole = accRole.lower()
		role=IAccessibleHandler.IAccessibleRolesToNVDARoles.get(accRole,controlTypes.ROLE_UNKNOWN)
		states=set(IAccessibleHandler.IAccessibleStatesToNVDAStates[x] for x in [1<<y for y in xrange(32)] if int(attrs.get('iaccessible::state_%s'%x,0)) and x in IAccessibleHandler.IAccessibleStatesToNVDAStates)
		newAttrs=textHandler.ControlField()
		newAttrs.update(attrs)
		newAttrs['role']=role
		newAttrs['states']=states
		return newAttrs

class AdobeAcrobat(VirtualBuffer):
	TextInfo = AdobeAcrobat_TextInfo

	def __init__(self,rootNVDAObject):
		super(AdobeAcrobat,self).__init__(rootNVDAObject,backendLibPath=r"lib\VBufBackend_adobeAcrobat.dll")
		self._lastFocusTime = 0

	def isNVDAObjectInVirtualBuffer(self,obj):
		if self.rootNVDAObject.windowHandle==obj.windowHandle:
			return True
		return False

	def isAlive(self):
		root=self.rootNVDAObject
		if not root:
			return False
		states=root.states
		if not winUser.isWindow(root.windowHandle) or controlTypes.STATE_READONLY not in states:
			return False
		return True

	def getNVDAObjectFromIdentifier(self, docHandle, ID):
		return NVDAObjects.IAccessible.getNVDAObjectFromEvent(docHandle, IAccessibleHandler.OBJID_CLIENT, ID)

	def getIdentifierFromNVDAObject(self,obj):
		docHandle=obj.windowHandle
		ID=obj.event_childID
		return docHandle,ID

	def event_focusEntered(self,obj,nextHandler):
		if self.passThrough:
			nextHandler()

	def _searchableAttribsForNodeType(self,nodeType):
		if nodeType=="link":
			attrs={"IAccessible::role":[IAccessibleHandler.ROLE_SYSTEM_LINK]}
		elif nodeType=="focusable":
			attrs={"IAccessible::state_%s"%IAccessibleHandler.STATE_SYSTEM_FOCUSABLE:[1]}
		else:
			return None
		return attrs

	def _shouldSetFocusToObj(self, obj):
		return controlTypes.STATE_FOCUSABLE in obj.states

	def _activateField(self, info):
		obj = info.NVDAObjectAtStart
		if self.shouldPassThrough(obj):
			obj.setFocus()
			self.passThrough = True
			virtualBufferHandler.reportPassThrough(self)
		else:
			obj.doAction(0)

	def _postGainFocus(self, obj):
		super(AdobeAcrobat, self)._postGainFocus(obj)
		self._lastFocusTime = time.time()

	def event_valueChange(self, obj, nextHandler):
		if obj.event_childID == 0:
			return nextHandler()
		if time.time() - self._lastFocusTime < 0.05:
			# A focus change will often cause the document to scroll, which will steal the caret from the focus.
			# Therefore, ignore scrolling if it is within a short time of the last focus change.
			return nextHandler()
		if not self._handleScrollTo(obj):
			return nextHandler()
