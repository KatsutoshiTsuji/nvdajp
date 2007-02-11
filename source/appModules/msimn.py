import audio
import winUser
import _default

class appModule(_default.appModule):

	def event_IAccessible_gainFocus(self,window,objectID,childID):
		controlID=winUser.getControlID(window)
		parent=winUser.getAncestor(window,winUser.GA_PARENT)
		parentClassName=winUser.getClassName(parent)
		if parentClassName=="OE_Envelope":
			if controlID==1001:
				audio.speakText(_("To:"))
			elif controlID==1003:
				audio.speakText(_("CC:"))
			elif controlID==1026:
				audio.speakText(_("BCC:"))
			elif controlID==1004:
				audio.speakText(_("Subject:"))
			elif controlID==1005:
				audio.speakText(_("From:"))
			elif controlID==1037:
				audio.speakText(_("From:"))
			elif controlID==1016:
				audio.speakText(_("Date:"))
			elif controlID==1000:
				audio.speakText(_("Attachments"))
		return False
