from . import VirtualBuffer, VirtualBufferTextInfo
import controlTypes
import NVDAObjects.IAccessible
import winUser
import IAccessibleHandler
from logHandler import log
import textHandler

class AdobeAcrobat_TextInfo(VirtualBufferTextInfo):
	stdNamesToRoles = {
		# part? art?
		"sect": controlTypes.ROLE_SECTION,
		"div": controlTypes.ROLE_SECTION,
		"blockquote": controlTypes.ROLE_BLOCKQUOTE,
		"caption": controlTypes.ROLE_CAPTION,
		# toc? toci? index? nonstruct? private? 
		"l": controlTypes.ROLE_LIST,
		"li": controlTypes.ROLE_LISTITEM,
		"lbl": controlTypes.ROLE_LABEL,
		# lbody
		"p": controlTypes.ROLE_PARAGRAPH,
		"h": controlTypes.ROLE_HEADING,
		# h1 to h6 handled separately
		# span, quote, note, reference, bibentry, code, figure, formula
		"form": controlTypes.ROLE_FORM,
	}

	def _normalizeControlField(self,attrs):
		role = None
		level = None

		stdName = attrs.get("acrobat::stdname", "").lower()
		if "h1" <= stdName <= "h6":
			role = controlTypes.ROLE_HEADING
			level = stdName[1]
		if not role:
			try:
				role = self.stdNamesToRoles[stdName]
			except KeyError:
				pass
	
		if not role:
			accRole=attrs['iaccessible::role']
			if accRole.isdigit():
				accRole=int(accRole)
			else:
				accRole = accRole.lower()
			if accRole == IAccessibleHandler.ROLE_SYSTEM_COLUMNHEADER:
				# Treat column headers just like any other cell.
				accRole = IAccessibleHandler.ROLE_SYSTEM_CELL
			role=IAccessibleHandler.IAccessibleRolesToNVDARoles.get(accRole,controlTypes.ROLE_UNKNOWN)

		states=set(IAccessibleHandler.IAccessibleStatesToNVDAStates[x] for x in [1<<y for y in xrange(32)] if int(attrs.get('iaccessible::state_%s'%x,0)) and x in IAccessibleHandler.IAccessibleStatesToNVDAStates)

		newAttrs=textHandler.ControlField()
		newAttrs.update(attrs)
		newAttrs['role']=role
		newAttrs['states']=states
		if level:
			newAttrs["level"] = level
		return newAttrs

class AdobeAcrobat(VirtualBuffer):
	TextInfo = AdobeAcrobat_TextInfo

	def __init__(self,rootNVDAObject):
		super(AdobeAcrobat,self).__init__(rootNVDAObject,backendLibPath=r"lib\VBufBackend_adobeAcrobat.dll")

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
		elif nodeType=="table":
			attrs={"IAccessible::role":[IAccessibleHandler.ROLE_SYSTEM_TABLE]}
		elif nodeType.startswith("heading") and nodeType[7:].isdigit():
			attrs = {"acrobat::stdname": ["H%s" % nodeType[7:]]}
		elif nodeType == "heading":
			attrs = {"acrobat::stdname": ["H1", "H2", "H3", "H4", "H5", "H6"]}
		elif nodeType=="focusable":
			attrs={"IAccessible::state_%s"%IAccessibleHandler.STATE_SYSTEM_FOCUSABLE:[1]}
		else:
			return None
		return attrs

	def _shouldSetFocusToObj(self, obj):
		return controlTypes.STATE_FOCUSABLE in obj.states

	def event_valueChange(self, obj, nextHandler):
		if obj.event_childID == 0:
			return nextHandler()
		if not self._handleScrollTo(obj):
			return nextHandler()
