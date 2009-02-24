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

class Gecko_ia2_TextInfo(VirtualBufferTextInfo):

	def _normalizeControlField(self,attrs):
		accRole=attrs['iaccessible::role']
		accRole=int(accRole) if accRole.isdigit() else accRole
		role=IAccessibleHandler.IAccessibleRolesToNVDARoles.get(accRole,controlTypes.ROLE_UNKNOWN)
		if attrs.get('iaccessible2::attribute_tag',"").lower()=="blockquote":
			role=controlTypes.ROLE_BLOCKQUOTE
		states=set(IAccessibleHandler.IAccessibleStatesToNVDAStates[x] for x in [1<<y for y in xrange(32)] if int(attrs.get('iaccessible::state_%s'%x,0)) and x in IAccessibleHandler.IAccessibleStatesToNVDAStates)
		states|=set(IAccessibleHandler.IAccessible2StatesToNVDAStates[x] for x in [1<<y for y in xrange(32)] if int(attrs.get('iaccessible2::state_%s'%x,0)) and x in IAccessibleHandler.IAccessible2StatesToNVDAStates)
		defaultAction=attrs.get('defaultaction','')
		if defaultAction=="click":
			states.add(controlTypes.STATE_CLICKABLE)
		if role==controlTypes.ROLE_LINK and controlTypes.STATE_LINKED not in states:
			# This is a named link destination, not a link which can be activated. The user doesn't care about these.
			role=controlTypes.ROLE_TEXTFRAME
		level=attrs.get('iaccessible2::attribute_level',"")
		newAttrs=textHandler.ControlField()
		newAttrs.update(attrs)
		newAttrs['role']=role
		newAttrs['states']=states
		if level is not "" and level is not None:
			newAttrs['level']=level
		return newAttrs

class Gecko_ia2(VirtualBuffer):

	TextInfo=Gecko_ia2_TextInfo

	def __init__(self,rootNVDAObject):
		super(Gecko_ia2,self).__init__(rootNVDAObject,backendLibPath=r"lib\VBufBackend_gecko_ia2.dll")
		self._lastFocusIdentifier=(0,0)

	def isNVDAObjectInVirtualBuffer(self,obj):
		#Special code to handle Mozilla combobox lists
		if obj.windowClassName.startswith('Mozilla') and winUser.getWindowStyle(obj.windowHandle)&winUser.WS_POPUP:
			parent=obj.parent
			while parent and parent.windowHandle==obj.windowHandle:
				parent=parent.parent
			if parent:
				obj=parent.parent
		if not (isinstance(obj,NVDAObjects.IAccessible.IAccessible) and isinstance(obj.IAccessibleObject,IAccessibleHandler.IAccessible2)) or not obj.windowClassName.startswith('Mozilla') or not winUser.isDescendantWindow(self.rootNVDAObject.windowHandle,obj.windowHandle):
			return False
		if self.rootNVDAObject.windowHandle==obj.windowHandle:
			ID=obj.IAccessibleObject.uniqueID
			try:
				self.rootNVDAObject.IAccessibleObject.accChild(ID)
			except:
				return False
			return True
		else:
			return True

	def isAlive(self):
		root=self.rootNVDAObject
		if not root:
			return False
		states=root.states
		if not winUser.isWindow(root.windowHandle) or controlTypes.STATE_DEFUNCT in states or controlTypes.STATE_READONLY not in states:
			return False
		try:
			if not NVDAObjects.IAccessible.getNVDAObjectFromEvent(root.windowHandle,IAccessibleHandler.OBJID_CLIENT,root.IAccessibleObject.uniqueID):
				return False
		except:
			return False
		return True

	def getNVDAObjectFromIdentifier(self, docHandle, ID):
		return NVDAObjects.IAccessible.getNVDAObjectFromEvent(docHandle, IAccessibleHandler.OBJID_CLIENT, ID)

	def getIdentifierFromNVDAObject(self,obj):
		docHandle=obj.IAccessibleObject.windowHandle
		ID=obj.IAccessibleObject.uniqueID
		return docHandle,ID

	def event_focusEntered(self,obj,nextHandler):
		if self.passThrough:
			 nextHandler()

	def event_gainFocus(self,obj,nextHandler):
		try:
			docHandle=obj.IAccessibleObject.windowHandle
			ID=obj.IAccessibleObject.uniqueID
		except:
			return nextHandler()
		if not self.passThrough and self._lastFocusIdentifier==(docHandle,ID):
			# This was the last non-document node with focus, so don't handle this focus event.
			# Otherwise, if the user switches away and back to this document, the cursor will jump to this node.
			# This is not ideal if the user was positioned over a node which cannot receive focus.
			return
		if self.VBufHandle is None:
			return nextHandler()
		if obj==self.rootNVDAObject:
			if self.passThrough:
				return nextHandler()
			return 
		if obj.role==controlTypes.ROLE_DOCUMENT and not self.passThrough:
			return
		self._lastFocusIdentifier=(docHandle,ID)
		#We only want to update the caret and speak the field if we're not in the same one as before
		oldInfo=self.makeTextInfo(textHandler.POSITION_CARET)
		try:
			oldDocHandle,oldID=oldInfo.fieldIdentifierAtStart
		except:
			oldDocHandle=oldID=0
		if (docHandle!=oldDocHandle or ID!=oldID) and ID!=0:
			try:
				start,end=VBufClient_getBufferOffsetsFromFieldIdentifier(self.VBufHandle,docHandle,ID)
			except:
				# This object is not in the virtual buffer, even though it resides beneath the document.
				# Automatic pass through should be enabled in certain circumstances where this occurs.
				if not self.passThrough and self.shouldPassThrough(obj,reason=speech.REASON_FOCUS):
					self.passThrough=True
					virtualBufferHandler.reportPassThrough(self)
				return nextHandler()
			newInfo=self.makeTextInfo(textHandler.Offsets(start,end))
			startToStart=newInfo.compareEndPoints(oldInfo,"startToStart")
			startToEnd=newInfo.compareEndPoints(oldInfo,"startToEnd")
			endToStart=newInfo.compareEndPoints(oldInfo,"endToStart")
			endToEnd=newInfo.compareEndPoints(oldInfo,"endToEnd")
			if (startToStart<0 and endToEnd>0) or (startToStart>0 and endToEnd<0) or endToStart<=0 or startToEnd>0:
				if not self.passThrough:
					# If pass-through is disabled, cancel speech, as a focus change should cause page reading to stop.
					# This must be done before auto-pass-through occurs, as we want to stop page reading even if pass-through will be automatically enabled by this focus change.
					speech.cancelSpeech()
				self.passThrough=self.shouldPassThrough(obj,reason=speech.REASON_FOCUS)
				if not self.passThrough:
					# We read the info from the buffer instead of the control itself.
					speech.speakTextInfo(newInfo,reason=speech.REASON_FOCUS)
					# However, we still want to update the speech property cache so that property changes will be spoken properly.
					speech.speakObject(obj,speech.REASON_ONLYCACHE)
				else:
					nextHandler()
				newInfo.collapse()
				self._set_selection(newInfo,reason=speech.REASON_FOCUS)
		else:
			# The virtual buffer caret was already at the focused node.
			if not self.passThrough:
				# This focus change was caused by a virtual caret movement, so don't speak the focused node to avoid double speaking.
				# However, we still want to update the speech property cache so that property changes will be spoken properly.
				speech.speakObject(obj,speech.REASON_ONLYCACHE)
			else:
				return nextHandler()
		if hasattr(obj,'IAccessibleTextObject'):
			# We aren't passing this event to the NVDAObject, so we need to do this ourselves.
			obj.initAutoSelectDetection()

	def _shouldSetFocusToObj(self, obj):
		return controlTypes.STATE_FOCUSABLE in obj.states and obj.role!=controlTypes.ROLE_EMBEDDEDOBJECT

	def _activateField(self,docHandle,ID):
		try:
			obj=NVDAObjects.IAccessible.getNVDAObjectFromEvent(docHandle,IAccessibleHandler.OBJID_CLIENT,ID)
			if self.shouldPassThrough(obj):
				obj.setFocus()
				self.passThrough=True
				virtualBufferHandler.reportPassThrough(self)
			else: #Just try performing the default action of the object, or of one of its ancestors
				try:
					action=obj.IAccessibleObject.accDefaultAction(obj.IAccessibleChildID)
					if not action:
						log.debugWarning("no default action for object")
						raise RuntimeError("need an action")
					try:
						obj.IAccessibleObject.accDoDefaultAction(obj.IAccessibleChildID)
					except:
						log.debugWarning("error in calling accDoDefaultAction",exc_info=True)
						raise RuntimeError("error in accDoDefaultAction")
				except:
					log.debugWarning("could not programmatically activate field, trying mouse")
					l=obj.location
					if l:
						x=(l[0]+l[2]/2)
						y=l[1]+(l[3]/2) 
						oldX,oldY=winUser.getCursorPos()
						winUser.setCursorPos(x,y)
						winUser.mouse_event(winUser.MOUSEEVENTF_LEFTDOWN,0,0,None,None)
						winUser.mouse_event(winUser.MOUSEEVENTF_LEFTUP,0,0,None,None)
						winUser.setCursorPos(oldX,oldY)
					else:
						log.debugWarning("no location for field")
		except:
			log.debugWarning("Error activating field",exc_info=True)
			pass

	def _searchableAttribsForNodeType(self,nodeType):
		if nodeType.startswith('heading') and nodeType[7:].isdigit():
			attrs={"IAccessible::role":[IAccessibleHandler.IA2_ROLE_HEADING],"IAccessible2::attribute_level":[nodeType[7:]]}
		elif nodeType=="heading":
			attrs={"IAccessible::role":[IAccessibleHandler.IA2_ROLE_HEADING]}
		elif nodeType=="table":
			attrs={"IAccessible::role":[IAccessibleHandler.ROLE_SYSTEM_TABLE]}
		elif nodeType=="link":
			attrs={"IAccessible::role":[IAccessibleHandler.ROLE_SYSTEM_LINK],"IAccessible::state_%d"%IAccessibleHandler.STATE_SYSTEM_LINKED:[1]}
		elif nodeType=="visitedLink":
			attrs={"IAccessible::role":[IAccessibleHandler.ROLE_SYSTEM_LINK],"IAccessible::state_%d"%IAccessibleHandler.STATE_SYSTEM_TRAVERSED:[1]}
		elif nodeType=="unvisitedLink":
			attrs={"IAccessible::role":[IAccessibleHandler.ROLE_SYSTEM_LINK],"IAccessible::state_%d"%IAccessibleHandler.STATE_SYSTEM_LINKED:[1],"IAccessible::state_%d"%IAccessibleHandler.STATE_SYSTEM_TRAVERSED:[None]}
		elif nodeType=="formField":
			attrs={"IAccessible::role":[IAccessibleHandler.ROLE_SYSTEM_PUSHBUTTON,IAccessibleHandler.ROLE_SYSTEM_RADIOBUTTON,IAccessibleHandler.ROLE_SYSTEM_CHECKBUTTON,IAccessibleHandler.ROLE_SYSTEM_COMBOBOX,IAccessibleHandler.ROLE_SYSTEM_LIST,IAccessibleHandler.ROLE_SYSTEM_OUTLINE,IAccessibleHandler.ROLE_SYSTEM_TEXT],"IAccessible::state_%s"%IAccessibleHandler.STATE_SYSTEM_READONLY:[None]}
		elif nodeType=="list":
			attrs={"IAccessible::role":[IAccessibleHandler.ROLE_SYSTEM_LIST]}
		elif nodeType=="listItem":
			attrs={"IAccessible::role":[IAccessibleHandler.ROLE_SYSTEM_LISTITEM]}
		elif nodeType=="button":
			attrs={"IAccessible::role":[IAccessibleHandler.ROLE_SYSTEM_PUSHBUTTON]}
		elif nodeType=="edit":
			attrs={"IAccessible::role":[IAccessibleHandler.ROLE_SYSTEM_TEXT],"IAccessible::state_%s"%IAccessibleHandler.STATE_SYSTEM_READONLY:[None]}
		elif nodeType=="frame":
			attrs={"IAccessible::role":[IAccessibleHandler.IA2_ROLE_INTERNAL_FRAME]}
		elif nodeType=="separator":
			attrs={"IAccessible::role":[IAccessibleHandler.ROLE_SYSTEM_SEPARATOR]}
		elif nodeType=="radioButton":
			attrs={"IAccessible::role":[IAccessibleHandler.ROLE_SYSTEM_RADIOBUTTON]}
		elif nodeType=="comboBox":
			attrs={"IAccessible::role":[IAccessibleHandler.ROLE_SYSTEM_COMBOBOX]}
		elif nodeType=="checkBox":
			attrs={"IAccessible::role":[IAccessibleHandler.ROLE_SYSTEM_CHECKBUTTON]}
		elif nodeType=="graphic":
			attrs={"IAccessible::role":[IAccessibleHandler.ROLE_SYSTEM_GRAPHIC]}
		elif nodeType=="blockQuote":
			attrs={"IAccessible2::attribute_tag":["BLOCKQUOTE"]}
		elif nodeType=="focusable":
			attrs={"IAccessible::state_%s"%IAccessibleHandler.STATE_SYSTEM_FOCUSABLE:[1]}
		else:
			return None
		return attrs

	def event_stateChange(self,obj,nextHandler):
		if not self.isAlive():
			return virtualBufferHandler.killVirtualBuffer(self)
		return nextHandler()

	def event_scrollingStart(self,obj,nextHandler):
		if self.VBufHandle is None:
			return nextHandler()
		#We only want to update the caret and speak the field if we're not in the same one as before
		oldInfo=self.makeTextInfo(textHandler.POSITION_CARET)
		try:
			oldDocHandle,oldID=oldInfo.fieldIdentifierAtStart
		except:
			oldDocHandle=oldID=0
		docHandle=obj.IAccessibleObject.windowHandle
		ID=obj.IAccessibleObject.uniqueID
		if (docHandle!=oldDocHandle or ID!=oldID) and ID!=0:
			try:
				start,end=VBufClient_getBufferOffsetsFromFieldIdentifier(self.VBufHandle,docHandle,ID)
			except:
				#log.error("VBufClient_getBufferOffsetsFromFieldIdentifier",exc_info=True)
				return nextHandler()
			newInfo=self.makeTextInfo(textHandler.Offsets(start,end))
			startToStart=newInfo.compareEndPoints(oldInfo,"startToStart")
			startToEnd=newInfo.compareEndPoints(oldInfo,"startToEnd")
			endToStart=newInfo.compareEndPoints(oldInfo,"endToStart")
			endToEnd=newInfo.compareEndPoints(oldInfo,"endToEnd")
			if (startToStart<0 and endToEnd>0) or (startToStart>0 and endToEnd<0) or endToStart<=0 or startToEnd>0:
				speech.speakTextInfo(newInfo,reason=speech.REASON_FOCUS)
				newInfo.collapse()
				self.selection=newInfo
