#text.py
#A part of NonVisual Desktop Access (NVDA)
#Copyright (C) 2006-2007 NVDA Contributors <http://www.nvda-project.org/>
#This file is covered by the GNU General Public License.
#See the file COPYING for more details.

import baseObject

#exceptions
class E_noRelatedUnit(RuntimeError):
	pass

#Unit constants
UNIT_CHARACTER="character"
UNIT_WORD="word"
UNIT_LINE="line"
UNIT_PARAGRAPH="paragraph"
UNIT_PAGE="page"
UNIT_TABLE="table"
UNIT_ROW="row"
UNIT_COLUMN="column"
UNIT_CELL="cell"
UNIT_SCREEN="screen"
UNIT_STORY="story"

#Position constants
POSITION_FIRST="first"
POSITION_CARET="caret"
POSITION_SELECTION="selection"
POSITION_LAST="last"

#Unit relationship string constants
UNITRELATION_NEXT="next"
UNITRELATION_PREVIOUS="previous"
UNITRELATION_header="header"
UNITRELATION_FOOTER="footer"
UNITRELATION_FIRST="first"
UNITRELATION_LAST="last"
UNITRELATION_LINKEDTO="linkedTo"

class TextInfo(baseObject.autoPropertyObject):
	"""Contains information about the text at the given position or unit
@ivar basePosition: the position (offset or point) this object was based on. Can also be one of the position constants to be caret or selection
@type basePosition: int, tuple or string
@ivar obj: The NVDA object this object is representing text from
@type: L{NVDAObject}
@ivar unit: The unit (character, word, line, paragraph) which this object has been expanded to
@type unit: string
@ivar endPosition: the end position (offset or point) that completes the range this object represents (if a unit has not been set).
@type endPosition: int, tuple or string
"""
 
	def __init__(self,obj,position,expandToUnit=None,limitToUnit=None,endPosition=None):
		"""
@param position: the position (offset or point) this object was based on. Can also be one of the position constants to be caret or selection
@type position: int, tuple or string
@param obj: The NVDA object this object is representing text from
@type: L{NVDAObject}
@param expandToUnit: The unit (character, word, line, paragraph) which this object has been expanded to
@type expandToUnit: string
@param limitToUnit: the unit that all navigation is limited to
@type limitToUnit: string 
@param endPosition: the end position (offset or point) that completes the range this object represents (if a unit has not been set).
@type endPosition: int, tuple or string
"""
		if (expandToUnit is not None and endPosition is not None) or (expandToUnit is None and endPosition is None):
			raise ValueError("Please give a unit or an endPosition.") 
		self.obj=obj
		self.basePosition=position
		self.unit=expandToUnit
		self.limitUnit=limitToUnit
		self.endPosition=endPosition

	def _get_startOffset(self):
		"""
@returns: The 0 based offset where this text is positioned in the object
@rtype: int
"""
		raise NotImplementedError

	def _get_endOffset(self):
		"""
@returns: The 0 based offset where this text ends, in the object
@rtype: int
"""
		raise NotImplementedError

	def _get_startPoint(self):
		"""
@returns: The screen x,y point where this text starts
@rtype: tuple 
"""
		raise NotImplementedError

	def _get_endPoint(self):
		"""
@returns: The screen x,y point where this text ends
@rtype: tuple
"""
		raise NotImplementedError

	def _get_text(self):
		"""
@returns: The text with in the set range. It is not garenteed to be the exact length of the range in offsets
@rtype: string
"""
		raise NotImplementedError

	def _get_formattedText(self):
		"""
@returns: The text (containing formatting markup) with in the set range
@rtype: string
"""
		raise NotImplementedError

	def _get_FGColor(self):
		"""
@returns: The foreground color at the start of the set range
@rtype: string
"""
		raise NotImplementedError

	def _get_BGColor(self):
		"""
@returns: The background color at the start of the set range
@rtype: string
"""
		raise NotImplementedError

	def _get_format(self):
		"""
@returns: The format at the start of the set range
@rtype: dict (string:string)
"""
		raise NotImplementedError

	def _get_inUnit(self):
		"""
@returns: whether this range is in the specified unit type
@rtype: boolean
"""
		raise NotImplementedError

	def _get_unitNumber(self):
		"""
@returns: The 1-based index of this unit, out of all the units of this type in the object
@rtype: int
"""  
		raise NotImplementedError

	def _get_unitCount(self):
		"""
@returns: the number of units of this type in the object
@rtype: int
"""
		raise NotImplementedError

	def getRelatedUnit(self,relation):
		"""
Locates another unit of this type with the given relation
@param relation: relationship type constant 
@type param: string
@returns: a new textInfo object set to the new range found with the unit relationship
@rtype: L{TextInfo}
"""
		raise NotImplementedError

def findStartOfLine(text,offset,lineLength=None):
	if offset>=len(text):
		raise ValueError("Offset %d is too high for text of length %d"%(offset,len(text)))
	start=offset
	if isinstance(lineLength,int):
		return offset-(offset%lineLength)
	if text[start]=='\n' and start>=0 and text[start-1]=='\r':
		start-=1
	start=text.rfind('\n',0,offset)
	if start<0:
		start=text.rfind('\r',0,offset)
	if start<0:
		start=-1
	return start+1

def findEndOfLine(text,offset,lineLength=None):
	if offset>=len(text):
		raise ValueError("Offset %d is too high for text of length %d"%(offset,len(text)))
	if isinstance(lineLength,int):
		return (offset-(offset%lineLength)+lineLength)
	end=offset
	if text[end]!='\n':
		end=text.find('\n',offset)
	if end<0:
		if text[offset]!='\r':
			end=text.find('\r',offset)
	if end<0:
		end=len(text)-1
	return end+1

def findStartOfWord(text,offset,lineLength=None):
	if offset>=len(text):
		raise ValueError("Offset %d is too high for text of length %d"%(offset,len(text)))
	lineStart=findStartOfLine(text,offset,lineLength=lineLength)
	while offset>lineStart and text[offset].isspace():
		offset-=1
	if not text[offset].isalnum():
		return offset
	else:
		while offset>lineStart and text[offset-1].isalnum():
			offset-=1
	return offset

def findEndOfWord(text,offset,lineLength=None):
	if offset>=len(text):
		raise ValueError("Offset %d is too high for text of length %d"%(offset,len(text)))
	lineEnd=findEndOfLine(text,offset,lineLength=lineLength)
	if text[offset].isalnum():
		while offset<lineEnd and text[offset].isalnum():
			offset+=1
	elif not text[offset].isspace() and not text[offset].isalnum():
		offset+=1
	while offset<lineEnd and text[offset].isspace():
		offset+=1
	return offset
