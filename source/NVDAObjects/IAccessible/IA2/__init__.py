import debug
import IA2Handler
from NVDAObjects.IAccessible import IAccessible

class IA2(IAccessible):

	def __init__(self,pacc,childID,windowHandle=None,origChildID=None,objectID=None):
		IAccessible.__init__(self,pacc,childID,windowHandle=windowHandle,origChildID=origChildID,objectID=objectID)
		try:
			self.IAccessibleTextObject=pacc.QueryInterface(IA2Handler.IA2Lib.IAccessibleText)
			try:
				self.IAccessibleEditableTextObject=pacc.QueryInterface(IA2Handler.IA2Lib.IAccessibleEditableText)
				[self.bindKey(keyName,scriptName) for keyName,scriptName in [
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
					("ExtendedDelete","text_delete"),
					("Back","text_backspace"),
				]]
			except:
				pass
		except:
			pass
		self.bindKey("extendedDown","text_moveByLine")

	def _get_text_characterCount(self):
		if not hasattr(self,"IAccessibleTextObject"):
			return IAccessible._get_text_characterCount(self)
		return self.IAccessibleTextObject.NCharacters

	def text_getText(self,start=None,end=None):
		if not hasattr(self,"IAccessibleTextObject"):
			return IAccessible.text_getText(self,start=start,end=end)
		start=start if start is not None else 0
		end=end if end is not None else self.text_characterCount
		if start<self.text_characterCount:
			return self.IAccessibleTextObject.Text(start,end)
		else:
			return None

	def _get_text_caretOffset(self):
		if not hasattr(self,"IAccessibleTextObject"):
			return IAccessible._get_text_caretOffset(self)
		return self.IAccessibleTextObject.CaretOffset
