import appModuleHandler
import NVDAObjects
import audio

class appModule(appModuleHandler.appModule):

	def __init__(self,*args):
		appModuleHandler.appModule.__init__(self,*args)
		self._lastValue=None

	def event_IAccessible_valueChange(self,window,objectID,childID,nextHandler):
		obj=NVDAObjects.window.NVDAObject_window(window)
		if obj.windowClassName=="Edit" and obj.windowControlID==403:
			text=obj.windowText[0:-1]
			text=text.rstrip()[0:-1]
			if text!=self._lastValue:
				audio.speakText(text)
				self._lastValue=text
		else:
			nextHandler(window,objectID,childID)

