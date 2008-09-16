#braille.py
#A part of NonVisual Desktop Access (NVDA)
#Copyright (C) 2006-2008 NVDA Contributors <http://www.nvda-project.org/>
#This file is covered by the GNU General Public License.
#See the file COPYING for more details.

import itertools
import os
import wx
import louis
import baseObject
import config
from logHandler import log
import controlTypes
import api
import textHandler

__path__ = ["brailleDisplayDrivers"]

#: The directory in which liblouis braille tables are located.
TABLES_DIR = r"louis\tables"

def _getDisplayDriver(name):
	return __import__(name,globals(),locals(),[]).BrailleDisplayDriver

def getDisplayList():
	displayList = []
	for name in (os.path.splitext(x)[0] for x in os.listdir(__path__[0]) if (x.endswith('.py') and not x.startswith('_'))):
		try:
			display = _getDisplayDriver(name)
			if display.check():
				displayList.append((display.name, display.description))
		except:
			pass
	return displayList

class Region(object):
	"""A region of braille to be displayed.
	Each portion of braille to be displayed is represented by a region.
	The region is responsible for retrieving its text and cursor position, translating it into braille cells and handling cursor routing requests relative to its braille cells.
	The L{BrailleBuffer} containing this region will call L{update} and expect that L{brailleCells} and L{brailleCursorPos} will be set appropriately.
	L{routeTo} will be called to handle a cursor routing request.
	"""

	def __init__(self):
		#: The original, raw text of this region.
		self.rawText = ""
		#: The position of the cursor in L{rawText}, C{None} if the cursor is not in this region.
		#: @type: int
		self.cursorPos = None
		#: The translated braille representation of this region.
		#: @type: [int, ...]
		self.brailleCells = []
		#: A list mapping positions in L{rawText} to positions in L{brailleCells}.
		#: @type: [int, ...]
		self.rawToBraillePos = []
		#: A list mapping positions in L{brailleCells} to positions in L{rawText}.
		#: @type: [int, ...]
		self.brailleToRawPos = []
		#: The position of the cursor in L{brailleCells}, C{None} if the cursor is not in this region.
		#: @type: int
		self.brailleCursorPos = None

	def update(self):
		"""Update this region.
		Subclasses should extend this to update L{rawText} and L{cursorPos} if necessary.
		The base class method handles translation of L{rawText} into braille, placing the result in L{brailleCells}. L{rawToBraillePos} and L{brailleToRawPos} are updated according to the translation.
		L{brailleCursorPos} is similarly updated based on L{cursorPos}.
		@postcondition: L{brailleCells} and L{brailleCursorPos} are updated and ready for rendering.
		"""
		mode = louis.MODE.dotsIO
		if config.conf["braille"]["expandAtCursor"] and self.cursorPos is not None:
			mode |= louis.MODE.compbrlAtCursor
		braille, self.brailleToRawPos, self.rawToBraillePos, brailleCursorPos = louis.translate([os.path.join(TABLES_DIR, handler.translationTable)], unicode(self.rawText), mode=mode, cursorPos=self.cursorPos or 0)
		# liblouis gives us back a character string of cells, so convert it to a list of ints.
		# For some reason, the highest bit is set, so only grab the lower 8 bits.
		self.brailleCells = [ord(cell) & 255 for cell in braille]
		if self.cursorPos is not None:
			self.brailleCursorPos = brailleCursorPos

	def routeTo(self, braillePos):
		"""Handle a cursor routing request.
		For example, this might activate an object or move the cursor to the requested position.
		@param braillePos: The routing position in L{brailleCells}.
		@type braillePos: int
		@note: If routing the cursor, L{brailleToRawPos} can be used to translate L{braillePos} into a position in L{rawText}.
		"""
		pass

class TextRegion(Region):
	"""A simple region containing a string of text.
	"""

	def __init__(self, text):
		super(TextRegion, self).__init__()
		self.rawText = text

class NVDAObjectRegion(Region):
	"""A region to provide a braille representation of an NVDAObject.
	This region will update based on the current state of the associated NVDAObject.
	A cursor routing request will activate the object's default action.
	"""

	def __init__(self, obj, appendText=""):
		"""Constructor.
		@param obj: The associated NVDAObject.
		@type obj: L{NVDAObjects.NVDAObject}
		@param appendText: Text which should always be appended to the NVDAObject text, useful if this region will always precede other regions.
		@type appendText: str
		"""
		super(NVDAObjectRegion, self).__init__()
		self.obj = obj
		self.appendText = appendText

	def update(self):
		textList = []
		name = self.obj.name
		if name:
			textList.append(name)
		#TODO: Don't use speech stuff.
		textList.append(controlTypes.speechRoleLabels[self.obj.role])
		self.rawText = " ".join(textList) + self.appendText
		super(NVDAObjectRegion, self).update()

	def routeTo(self, braillePos):
		self.obj.doDefaultAction()

class TextInfoRegion(Region):

	def __init__(self, obj):
		super(TextInfoRegion, self).__init__()
		self.obj = obj

	def update(self):
		caret = self.obj.makeTextInfo(textHandler.POSITION_CARET)
		# Get the line at the caret.
		self._line = line = caret.copy()
		line.expand(textHandler.UNIT_LINE)
		# Not all text APIs support offsets, so we can't always get the offset of the caret relative to the start of the line.
		# Therefore, grab the line in two parts.
		# First, the chunk from the start of the line up to the caret.
		chunk = line.copy()
		chunk.collapse()
		chunk.setEndPoint(caret, "endToEnd")
		self.rawText = chunk.text
		# The cursor position is the length of this chunk, as its end is the caret.
		self.cursorPos = len(self.rawText)
		# Now, get the chunk from the caret to the end of the line.
		chunk.setEndPoint(line, "endToEnd")
		chunk.setEndPoint(caret, "startToStart")
		# Strip line ending characters, but add a space in case the caret is at the end of the line.
		self.rawText += chunk.text.rstrip("\r\n") + " "
		super(TextInfoRegion, self).update()

	def routeTo(self, braillePos):
		pos = self.brailleToRawPos[braillePos]
		# pos is relative to the start of the line.
		# Therefore, get the start of the line...
		dest = self._line.copy()
		dest.collapse()
		# and move pos characters from there.
		dest.move(textHandler.UNIT_CHARACTER, pos)
		dest.updateCaret()

class BrailleBuffer(baseObject.AutoPropertyObject):

	def __init__(self, handler):
		self.handler = handler
		#: The regions in this buffer.
		#: @type: [L{Region}, ...]
		self.regions = []
		#: The position of the cursor in L{brailleCells}, C{None} if no region contains the cursor.
		#: @type: int
		self.cursorPos = None
		#: The translated braille representation of the entire buffer.
		#: @type: [int, ...]
		self.brailleCells = []
		#: The position in L{brailleCells} where the display window starts (inclusive).
		#: @type: int
		self.windowStartPos = 0

	def clear(self):
		"""Clear the entire buffer.
		This removes all regions and resets the window position to 0.
		"""
		self.regions = []
		self.cursorPos = None
		self.brailleCursorPos = None
		self.brailleCells = []
		self.windowStartPos = 0

	def _get_regionsWithPositions(self):
		start = 0
		for region in self.regions:
			end = start + len(region.brailleCells)
			yield region, start, end
			start = end

	def bufferPosToRegionPos(self, bufferPos):
		for region, start, end in self.regionsWithPositions:
			if end > bufferPos:
				return region, bufferPos - start
		raise LookupError("No such position")

	def regionPosToBufferPos(self, region, pos):
		for testRegion, start, end in self.regionsWithPositions:
			if region == testRegion:
				if pos < end:
					return start + pos
		raise LookupError("No such position")

	def bufferPosToWindowPos(self, bufferPos):
		if not (self.windowStartPos <= bufferPos < self.windowEndPos):
			raise LookupError("Buffer position not in window")
		return bufferPos - self.windowStartPos

	def _get_windowEndPos(self):
		try:
			lineEnd = self.brailleCells.index(-1, self.windowStartPos)
		except ValueError:
			lineEnd = len(self.brailleCells)
		return min(lineEnd, self.windowStartPos + self.handler.displaySize)

	def _set_windowEndPos(self, endPos):
		lineStart = endPos - 1
		# Find the end of the previous line.
		while lineStart >= 0:
			if self.brailleCells[lineStart] == -1:
				break
			lineStart -= 1
		lineStart += 1
		self.windowStartPos = max(endPos - self.handler.displaySize, lineStart)

	def scrollForward(self):
		end = self.windowEndPos
		if end < len(self.brailleCells):
			self.windowStartPos = end
		self.updateDisplay()

	def scrollBack(self):
		start = self.windowStartPos
		if start > 0:
			self.windowEndPos = start
		self.updateDisplay()

	def scrollTo(self, region, pos):
		pos = self.regionPosToBufferPos(region, pos)
		if pos > self.windowEndPos:
			self.windowEndPos = pos + 1
		elif pos < self.windowStartPos:
			self.windowStartPos = pos
		self.updateDisplay()

	def focus(self, region):
		"""Bring the specified region into focus so that as much as possible of the region is visible.
		The region is usually placed at the start of the display.
		However, if there is extra space at the end of the display, the display is scrolled left so that as much as possible is displayed.
		@param region: The region to focus.
		@type region: L{Region}
		"""
		pos = self.regionPosToBufferPos(region, 0)
		self.windowStartPos = pos
		end = self.windowEndPos
		if end - pos < self.handler.displaySize:
			# We can fit more on the display while still keeping pos visible.
			# Force windowStartPos to be recalculated based on windowEndPos.
			self.windowEndPos = end

	def update(self, updateDisplay=True):
		self.brailleCells = []
		self.cursorPos = None
		start = 0
		for region in self.regions:
			cells = region.brailleCells
			self.brailleCells.extend(cells)
			if region.brailleCursorPos is not None:
				self.cursorPos = start + region.brailleCursorPos
			start += len(cells)
		if updateDisplay:
			self.updateDisplay()

	def updateDisplay(self):
		if self is self.handler.buffer:
			self.handler.update()

	def _get_cursorWindowPos(self):
		if self.cursorPos is None:
			return None
		try:
			return self.bufferPosToWindowPos(self.cursorPos)
		except LookupError:
			return None

	def _get_windowBrailleCells(self):
		return self.brailleCells[self.windowStartPos:self.windowEndPos]

	def routeTo(self, windowPos):
		pos = self.windowStartPos + windowPos
		if pos >= self.windowEndPos:
			return
		region, pos = self.bufferPosToRegionPos(pos)
		region.routeTo(pos)

def getContextRegionsForNVDAObject(obj):
	# TODO: Shouldn't be specific to the current focus.
	for parent in api.getFocusAncestors()[1:]:
		role=parent.role
		if role in (controlTypes.ROLE_UNKNOWN,controlTypes.ROLE_WINDOW,controlTypes.ROLE_SECTION,controlTypes.ROLE_TREEVIEWITEM,controlTypes.ROLE_LISTITEM,controlTypes.ROLE_PARAGRAPH,controlTypes.ROLE_PROGRESSBAR,controlTypes.ROLE_EDITABLETEXT,controlTypes.ROLE_MENUITEM):
			continue
		name=parent.name
		description=parent.description
		if role in (controlTypes.ROLE_PANEL,controlTypes.ROLE_PROPERTYPAGE,controlTypes.ROLE_TABLECELL,controlTypes.ROLE_TEXTFRAME,controlTypes.ROLE_SECTION) and not name and not description:
			continue
		states=parent.states
		if controlTypes.STATE_INVISIBLE in states or controlTypes.STATE_UNAVAILABLE in states:
			continue
		yield NVDAObjectRegion(parent, appendText=" ")

def getFocusRegionsForNVDAObject(obj):
	# TODO: Handle VirtualBuffers.
	useTextInfo = (obj.role == controlTypes.ROLE_EDITABLETEXT or controlTypes.STATE_EDITABLE in obj.states)
	yield NVDAObjectRegion(obj, appendText=" " if useTextInfo else "")
	if useTextInfo:
		yield TextInfoRegion(obj)

class BrailleHandler(baseObject.AutoPropertyObject):

	def __init__(self):
		self.translationTable = config.conf["braille"]["translationTable"]
		self.display = None
		self.displaySize = 0
		self.mainBuffer = BrailleBuffer(self)
		self.buffer = self.mainBuffer

	def setDisplayByName(self, name):
		if not name:
			self.display = None
			self.displaySize = 0
			return
		try:
			self.display = _getDisplayDriver(name)()
			self.displaySize = self.display.numCells
		except:
			log.error("Error initializing display driver", exc_info=True)
			self.setDisplayByName("noBraille")

	def update(self):
		self.display.display(self.buffer.windowBrailleCells)
		self.display.cursorPos = self.buffer.cursorWindowPos

	def handleGainFocus(self, obj):
		self.buffer.clear()
		for region in itertools.chain(getContextRegionsForNVDAObject(obj), getFocusRegionsForNVDAObject(obj)):
			self.buffer.regions.append(region)
			region.update()
		self.buffer.update(updateDisplay=False)
		# Last region should receive focus.
		self.buffer.focus(region)
		if region.cursorPos is not None:
			self.buffer.scrollTo(region, region.cursorPos)
		self.update()

	def handleCaretMove(self, obj):
		if not self.buffer.regions:
			return
		region = self.buffer.regions[-1]
		if region.obj is not obj:
			return
		region.update()
		self.buffer.update(updateDisplay=False)
		self.buffer.scrollTo(region, region.cursorPos)
		self.update()

def initialize():
	global handler
	handler = BrailleHandler()
	handler.setDisplayByName(config.conf["braille"]["display"])

def terminate():
	global handler
	handler = None

class BrailleDisplayDriver(baseObject.AutoPropertyObject):
	"""Abstract base braille display driver.
	Each braille display driver should be a separate Python module in the root brailleDisplayDrivers directory containing a BrailleDisplayDriver class which inherits from this base class.
	
	At a minimum, drivers must set L{name} and L{description} and override the L{check} method.
	"""
	#: The name of the braille display; must be the original module file name.
	#: @type: str
	name = ""
	#: A description of the braille display.
	#: @type: str
	description = ""

	@classmethod
	def check(cls):
		"""Determine whether this braille display is available.
		The display will be excluded from the list of available displays if this method returns C{False}.
		For example, if this display is not present, C{False} should be returned.
		@return: C{True} if this display is available, C{False} if not.
		@rtype: bool
		"""
		return False

	def _get_numCells(self):
		"""Obtain the number of braille cells on this  display.
		@return: The number of cells.
		@rtype: int
		"""
		# Zero wouldn't make sense even for a null device ;-)
		return 80

	def display(self, cells):
		"""Display the given braille cells.
		@param cells: The braille cells to display.
		@type cells: [int, ...]
		"""
		pass

	def _get_cursorPos(self):
		return None

	def _set_cursorPos(self, pos):
		pass

	def _get_cursorShape(self):
		return None

	def _set_cursorShape(self, shape):
		pass

	def _get_cursorBlinkRate(self):
		return 0

	def _set_cursorBlinkRate(self, rate):
		pass

class BrailleDisplayDriverWithCursor(BrailleDisplayDriver):
	"""Abstract base braille display driver which manages its own cursor.
	This should be used by braille display drivers where the display or underlying driver does not provide support for a cursor.
	Instead of overriding L{display}, subclasses should override L{_display}.
	"""

	def __init__(self):
		self._cursorPos = None
		self._cursorBlinkRate = 1000
		self._cursorBlinkUp = True
		self._cursorShape = 0xc0
		self._cells = []
		self._cursorBlinkTimer = None
		self._initCursor()

	def _initCursor(self):
		if self._cursorBlinkTimer:
			self._cursorBlinkTimer.Stop()
		self._cursorBlinkUp = True
		self._displayWithCursor()
		if self._cursorBlinkRate:
			self._cursorBlinkTimer = wx.PyTimer(self._blink)
			self._cursorBlinkTimer.Start(self._cursorBlinkRate)

	def _blink(self):
		self._cursorBlinkUp = not self._cursorBlinkUp
		self._displayWithCursor()

	def _get_cursorPos(self):
		return self._cursorPos

	def _set_cursorPos(self, pos):
		self._cursorPos = pos
		self._initCursor()

	def _get_cursorBlinkRate(self):
		return self._cursorBlinkRate

	def _set_cursorBlinkRate(self, rate):
		self._cursorBlinkRate = rate
		self._initCursor()

	def _get_cursorShape(self):
		return self._cursorShape

	def _set_cursorShape(self, shape):
		self._cursorShape = shape
		self._initCursor()

	def display(self, cells):
		# cells might not be the full length of the display.
		# Therefore, pad it with spaces to fill the display so that the cursor can lie beyond it.
		self._cells = cells + [0] * (self.numCells - len(cells))
		self._displayWithCursor()

	def _displayWithCursor(self):
		if not self._cells:
			return
		cells = list(self._cells)
		if self._cursorPos is not None and self._cursorBlinkUp:
			cells[self._cursorPos] |= self._cursorShape
		self._display(cells)

	def _display(self, cells):
		"""Actually display the given cells to the display.
		L{display} calls methods to handle the cursor representation as appropriate.
		However, this method (L{_display}) is called to actually display the final cells.
		"""
		pass
