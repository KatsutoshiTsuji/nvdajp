import appModuleHandler
import speech

class appModule(appModuleHandler.appModule):

	def __init__(self,*args):
		appModuleHandler.appModule.__init__(self,*args)
		self._lastValue=None

	def event_NVDAObject_init(self,obj):
		if obj.windowClassName=="Edit" and obj.windowControlID==403:
			obj.name="Display"

	def event_valueChange(self,obj,nextHandler):
		if obj.windowClassName=="Edit" and obj.windowControlID==403:
			text=obj.windowText[0:-1]
			text=text.rstrip()[0:-1]
			if text!=self._lastValue:
				speech.speakText(text)
				self._lastValue=text
		else:
			nextHandler()
