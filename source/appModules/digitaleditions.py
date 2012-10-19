#appModules/digitaleditions.py
#A part of NonVisual Desktop Access (NVDA)
#This file is covered by the GNU General Public License.
#See the file COPYING for more details.
#Copyright (C) 2011-2012 NV Access Limited

"""App module for Adobe Digital Editions
"""

import appModuleHandler
import controlTypes
from textInfos import DocumentWithPageTurns
from NVDAObjects.UIA import UIA
from keyboardHandler import KeyboardInputGesture

class BookContent(DocumentWithPageTurns, UIA):

	def turnPage(self, previous=False):
		try:
			# Find the slider which indicates the current page.
			pageSlider = self.parent.parent.next.lastChild
		except AttributeError:
			raise RuntimeError
		oldPos = pageSlider.value
		KeyboardInputGesture.fromName("pageUp" if previous else "pageDown").send()
		pageSlider.invalidateCache()
		if pageSlider.value == oldPos:
			# No more pages.
			raise RuntimeError

class AppModule(appModuleHandler.AppModule):

	def chooseNVDAObjectOverlayClasses(self, obj, clsList):
		if isinstance(obj, UIA) and obj.role == controlTypes.ROLE_DOCUMENT:
			clsList.insert(0, BookContent)
