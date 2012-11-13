#controlTypes.py
#A part of NonVisual Desktop Access (NVDA)
#This file is covered by the GNU General Public License.
#See the file COPYING for more details.
#Copyright (C) 2007-2012 NV Access Limited

ROLE_UNKNOWN=0
ROLE_WINDOW=1
ROLE_TITLEBAR=2
ROLE_PANE=3
ROLE_DIALOG=4
ROLE_CHECKBOX=5
ROLE_RADIOBUTTON=6
ROLE_STATICTEXT=7
ROLE_EDITABLETEXT=8
ROLE_BUTTON=9
ROLE_MENUBAR=10
ROLE_MENUITEM=11
ROLE_POPUPMENU=12
ROLE_COMBOBOX=13
ROLE_LIST=14
ROLE_LISTITEM=15
ROLE_GRAPHIC=16
ROLE_HELPBALLOON=17
ROLE_TOOLTIP=18
ROLE_LINK=19
ROLE_TREEVIEW=20
ROLE_TREEVIEWITEM=21
ROLE_TAB=22
ROLE_TABCONTROL=23
ROLE_SLIDER=24
ROLE_PROGRESSBAR=25
ROLE_SCROLLBAR=26
ROLE_STATUSBAR=27
ROLE_TABLE=28
ROLE_TABLECELL=29
ROLE_TABLECOLUMN=30
ROLE_TABLEROW=31
ROLE_TABLECOLUMNHEADER=32
ROLE_TABLEROWHEADER=33
ROLE_FRAME=34
ROLE_TOOLBAR=35
ROLE_DROPDOWNBUTTON=36
ROLE_CLOCK=37
ROLE_SEPARATOR=38
ROLE_FORM=39
ROLE_HEADING=40
ROLE_HEADING1=41
ROLE_HEADING2=42
ROLE_HEADING3=43
ROLE_HEADING4=44
ROLE_HEADING5=45
ROLE_HEADING6=46
ROLE_PARAGRAPH=47
ROLE_BLOCKQUOTE=48
ROLE_TABLEHEADER=49
ROLE_TABLEBODY=50
ROLE_TABLEFOOTER=51
ROLE_DOCUMENT=52
ROLE_ANIMATION=53
ROLE_APPLICATION=54
ROLE_BOX=55
ROLE_GROUPING=56
ROLE_PROPERTYPAGE=57
ROLE_CANVAS=58
ROLE_CAPTION=59
ROLE_CHECKMENUITEM=60,
ROLE_DATEEDITOR=61
ROLE_ICON=62
ROLE_DIRECTORYPANE=63
ROLE_EMBEDDEDOBJECT=64
ROLE_ENDNOTE=65
ROLE_FOOTER=66
ROLE_FOOTNOTE=67
ROLE_GLASSPANE=69
ROLE_HEADER=70
ROLE_IMAGEMAP=71
ROLE_INPUTWINDOW=72
ROLE_LABEL=73
ROLE_NOTE=74
ROLE_PAGE=75
ROLE_RADIOMENUITEM=76
ROLE_LAYEREDPANE=77
ROLE_REDUNDANTOBJECT=78
ROLE_ROOTPANE=79
ROLE_EDITBAR=80
ROLE_TERMINAL=82
ROLE_RICHEDIT=83
ROLE_RULER=84
ROLE_SCROLLPANE=85
ROLE_SECTION=86
ROLE_SHAPE=87
ROLE_SPLITPANE=88
ROLE_VIEWPORT=89
ROLE_TEAROFFMENU=90
ROLE_TEXTFRAME=91
ROLE_TOGGLEBUTTON=92
ROLE_BORDER=93
ROLE_CARET=94
ROLE_CHARACTER=95
ROLE_CHART=96
ROLE_CURSOR=97
ROLE_DIAGRAM=98
ROLE_DIAL=99
ROLE_DROPLIST=100
ROLE_SPLITBUTTON=101
ROLE_MENUBUTTON=102
ROLE_DROPDOWNBUTTONGRID=103
ROLE_EQUATION=104
ROLE_GRIP=105
ROLE_HOTKEYFIELD=106
ROLE_INDICATOR=107
ROLE_SPINBUTTON=108
ROLE_SOUND=109
ROLE_WHITESPACE=110
ROLE_TREEVIEWBUTTON=111
ROLE_IPADDRESS=112
ROLE_DESKTOPICON=113
ROLE_ALERT=114
ROLE_INTERNALFRAME=115
ROLE_DESKTOPPANE=116
ROLE_OPTIONPANE=117
ROLE_COLORCHOOSER=118
ROLE_FILECHOOSER=119
ROLE_FILLER=120
ROLE_MENU=121
ROLE_PANEL=122
ROLE_PASSWORDEDIT=123
ROLE_FONTCHOOSER=124
ROLE_LINE=125
ROLE_FONTNAME=126
ROLE_FONTSIZE=127
ROLE_BOLD=128
ROLE_ITALIC=129
ROLE_UNDERLINE=130
ROLE_FGCOLOR=131
ROLE_BGCOLOR=132
ROLE_SUPERSCRIPT=133
ROLE_SUBSCRIPT=134
ROLE_STYLE=135
ROLE_INDENT=136
ROLE_ALIGNMENT=137
ROLE_ALERT=138
ROLE_DATAGRID=139
ROLE_DATAITEM=140
ROLE_HEADERITEM=141
ROLE_THUMB=142
ROLE_CALENDAR=143

STATE_UNAVAILABLE=0X1
STATE_FOCUSED=0X2
STATE_SELECTED=0X4
STATE_BUSY=0X8
STATE_PRESSED=0X10
STATE_CHECKED=0X20
STATE_HALFCHECKED=0X40
STATE_READONLY=0X80
STATE_EXPANDED=0X100
STATE_COLLAPSED=0X200
STATE_INVISIBLE=0X400
STATE_VISITED=0X800
STATE_LINKED=0X1000
STATE_HASPOPUP=0X2000
STATE_PROTECTED=0X4000
STATE_REQUIRED=0X8000
STATE_DEFUNCT=0X10000
STATE_INVALID_ENTRY=0X20000
STATE_MODAL=0X40000
STATE_AUTOCOMPLETE=0x80000
STATE_MULTILINE=0X100000
STATE_ICONIFIED=0x200000
STATE_OFFSCREEN=0x400000
STATE_SELECTABLE=0x800000
STATE_FOCUSABLE=0x1000000
STATE_CLICKABLE=0x2000000
STATE_EDITABLE=0x4000000
STATE_CHECKABLE=0x8000000
STATE_DRAGGABLE=0x10000000
STATE_DRAGGING=0x20000000
STATE_DROPTARGET=0x40000000
STATE_SORTED=0x80000000
STATE_SORTED_ASCENDING=0x100000000
STATE_SORTED_DESCENDING=0x200000000
STATES_SORTED=frozenset([STATE_SORTED,STATE_SORTED_ASCENDING,STATE_SORTED_DESCENDING])
STATE_HASLONGDESC=0x400000000

roleLabels={
	ROLE_UNKNOWN:_("unknown"),
	ROLE_WINDOW:_("window"),
	ROLE_TITLEBAR:_("title bar"),
	ROLE_PANE:_("pane"),
	ROLE_DIALOG:_("dialog"),
	ROLE_CHECKBOX:_("check box"),
	ROLE_RADIOBUTTON:_("radio button"),
	ROLE_STATICTEXT:_("text"),
	ROLE_EDITABLETEXT:_("edit"),
	ROLE_BUTTON:_("button"),
	ROLE_MENUBAR:_("menu bar"),
	ROLE_MENUITEM:_("menu item"),
	ROLE_POPUPMENU:_("menu"),
	ROLE_COMBOBOX:_("combo box"),
	ROLE_LIST:_("list"),
	ROLE_LISTITEM:_("list item"),
	ROLE_GRAPHIC:_("graphic"),
	ROLE_HELPBALLOON:_("help balloon"),
	ROLE_TOOLTIP:_("tool tip"),
	ROLE_LINK:_("link"),
	ROLE_TREEVIEW:_("tree view"),
	ROLE_TREEVIEWITEM:_("tree view item"),
	# Translators: The word presented for tabs in a tab enabled window.
	ROLE_TAB: pgettext("controlType", "tab"),
	ROLE_TABCONTROL:_("tab control"),
	ROLE_SLIDER:_("slider"),
	ROLE_PROGRESSBAR:_("progress bar"),
	ROLE_SCROLLBAR:_("scroll bar"),
	ROLE_STATUSBAR:_("status bar"),
	ROLE_TABLE:_("table"),
	ROLE_TABLECELL:_("cell"),
	ROLE_TABLECOLUMN:_("column"),
	ROLE_TABLEROW:_("row"),
	ROLE_FRAME:_("frame"),
	ROLE_TOOLBAR:_("tool bar"),
	ROLE_TABLECOLUMNHEADER:_("column header"),
	ROLE_TABLEROWHEADER:_("row header"),
	ROLE_DROPDOWNBUTTON:_("drop down button"),
	ROLE_CLOCK:_("clock"),
	ROLE_SEPARATOR:_("separator"),
	ROLE_FORM:_("form"),
	ROLE_HEADING:_("heading"),
	ROLE_HEADING1:_("heading 1"),
	ROLE_HEADING2:_("heading 2"),
	ROLE_HEADING3:_("heading 3"),
	ROLE_HEADING4:_("heading 4"),
	ROLE_HEADING5:_("heading 5"),
	ROLE_HEADING6:_("heading 6"),
	ROLE_PARAGRAPH:_("paragraph"),
	# Translators: Presented for a section in a document which is a block quotation;
	# i.e. a long quotation in a separate paragraph distinguished by indentation, etc.
	# See http://en.wikipedia.org/wiki/Block_quotation
	ROLE_BLOCKQUOTE:_("block quote"),
	ROLE_TABLEHEADER:_("table header"),
	ROLE_TABLEBODY:_("table body"),
	ROLE_TABLEFOOTER:_("table footer"),
	ROLE_DOCUMENT:_("document"),
	ROLE_ANIMATION:_("animation"),
	ROLE_APPLICATION:_("application"),
	ROLE_BOX:_("box"),
	ROLE_GROUPING:_("grouping"),
	ROLE_PROPERTYPAGE:_("property page"),
	ROLE_CANVAS:_("canvas"),
	ROLE_CAPTION:_("caption"),
	ROLE_CHECKMENUITEM:_("check menu item"),
	ROLE_DATEEDITOR:_("date edit"),
	ROLE_ICON:_("icon"),
	ROLE_DIRECTORYPANE:_("directory pane"),
	ROLE_EMBEDDEDOBJECT:_("embedded object"),
	ROLE_ENDNOTE:_("end note"),
	ROLE_FOOTER:_("footer"),
	ROLE_FOOTNOTE:_("foot note"),
	# Translators: Reported for an object which is a glass pane; i.e.
	# a pane that is guaranteed to be on top of all panes beneath it.
	ROLE_GLASSPANE:_("glass pane"),
	ROLE_HEADER:_("header"),
	ROLE_IMAGEMAP:_("image map"),
	ROLE_INPUTWINDOW:_("input window"),
	ROLE_LABEL:_("label"),
	ROLE_NOTE:_("note"),
	ROLE_PAGE:_("page"),
	ROLE_RADIOMENUITEM:_("radio menu item"),
	ROLE_LAYEREDPANE:_("layered pane"),
	ROLE_REDUNDANTOBJECT:_("redundant object"),
	ROLE_ROOTPANE:_("root pane"),
	# Translators: May be reported for an editable text object in a toolbar.
	# This is deprecated and is not often (if ever) used.
	ROLE_EDITBAR:_("edit bar"),
	ROLE_TERMINAL:_("terminal"),
	ROLE_RICHEDIT:_("rich edit"),
	ROLE_RULER:_("ruler"),
	ROLE_SCROLLPANE:_("scroll pane"),
	ROLE_SECTION:_("section"),
	ROLE_SHAPE:_("shape"),
	ROLE_SPLITPANE:_("split pane"),
	# Translators: Reported for a view port; i.e. an object usually used in a scroll pane
	# which represents the portion of the entire data that the user can see.
	# As the user manipulates the scroll bars, the contents of the view port can change.
	ROLE_VIEWPORT:_("view port"),
	# Translators: Reported for an object that forms part of a menu system
	# but which can be undocked from or torn off the menu system
	# to exist as a separate window.
	ROLE_TEAROFFMENU:_("tear off menu"),
	ROLE_TEXTFRAME:_("text frame"),
	ROLE_TOGGLEBUTTON:_("toggle button"),
	ROLE_BORDER:_("border"),
	ROLE_CARET:_("caret"),
	ROLE_CHARACTER:_("character"),
	ROLE_CHART:_("chart"),
	ROLE_CURSOR:_("cursor"),
	ROLE_DIAGRAM:_("diagram"),
	ROLE_DIAL:_("dial"),
	ROLE_DROPLIST:_("drop list"),
	ROLE_SPLITBUTTON:_("split button"),
	ROLE_MENUBUTTON:_("menu button"),
	# Translators: Reported for a button which expands a grid when it is pressed.
	ROLE_DROPDOWNBUTTONGRID:_("drop down button grid"),
	ROLE_EQUATION:_("equation"),
	ROLE_GRIP:_("grip"),
	ROLE_HOTKEYFIELD:_("hot key field"),
	ROLE_INDICATOR:_("indicator"),
	ROLE_SPINBUTTON:_("spin button"),
	ROLE_SOUND:_("sound"),
	ROLE_WHITESPACE:_("white space"),
	ROLE_TREEVIEWBUTTON:_("tree view button"),
	ROLE_IPADDRESS:_("IP address"),
	ROLE_DESKTOPICON:_("desktop icon"),
	ROLE_ALERT:_("alert"),
	ROLE_INTERNALFRAME:_("IFrame"),
	ROLE_DESKTOPPANE:_("desktop pane"),
	ROLE_OPTIONPANE:_("option pane"),
	ROLE_COLORCHOOSER:_("color chooser"),
	ROLE_FILECHOOSER:_("file chooser"),
	ROLE_FILLER:_("filler"),
	ROLE_MENU:_("menu"),
	ROLE_PANEL:_("panel"),
	ROLE_PASSWORDEDIT:_("password edit"),
	ROLE_FONTCHOOSER:_("font chooser"),
	ROLE_LINE:_("line"),
	ROLE_FONTNAME:_("font name"),
	ROLE_FONTSIZE:_("font size"),
	ROLE_BOLD:_("bold"),
	ROLE_ITALIC:_("ITALIC"),
	ROLE_UNDERLINE:_("underline"),
	ROLE_FGCOLOR:_("foreground color"),
	ROLE_BGCOLOR:_("background color"),
	ROLE_SUPERSCRIPT:_("superscript"),
	ROLE_SUBSCRIPT:_("subscript"),
	ROLE_STYLE:_("style"),
	ROLE_INDENT:_("indent"),
	ROLE_ALIGNMENT:_("alignment"),
	ROLE_ALERT:_("alert"),
	ROLE_DATAGRID:_("data grid"),
	ROLE_DATAITEM:_("data item"),
	ROLE_HEADERITEM:_("header item"),
	ROLE_THUMB:_("thumb control"),
	ROLE_CALENDAR:_("calendar"),
}

stateLabels={
	STATE_UNAVAILABLE:_("unavailable"),
	STATE_FOCUSED:_("focused"),
	STATE_SELECTED:_("selected"),
	STATE_BUSY:_("busy"),
	STATE_PRESSED:_("pressed"),
	STATE_CHECKED:_("checked"),
	STATE_HALFCHECKED:_("half checked"),
	STATE_READONLY:_("read only"),
	STATE_EXPANDED:_("expanded"),
	STATE_COLLAPSED:_("collapsed"),
	STATE_INVISIBLE:_("invisible"),
	STATE_VISITED:_("visited"),
	STATE_LINKED:_("linked"),
	STATE_HASPOPUP:_("subMenu"),
	STATE_PROTECTED:_("protected"),
	STATE_REQUIRED:_("required"),
	# Translators: Reported when an object no longer exists in the user interface;
	# i.e. it is dead and is no longer usable.
	STATE_DEFUNCT:_("defunct"),
	STATE_INVALID_ENTRY:_("invalid entry"),
	STATE_MODAL:_("modal"),
	STATE_AUTOCOMPLETE:_("has auto complete"),
	STATE_MULTILINE:_("multi line"),
	STATE_ICONIFIED:_("iconified"),
	STATE_OFFSCREEN:_("off screen"),
	STATE_SELECTABLE:_("selectable"),
	STATE_FOCUSABLE:_("focusable"),
	STATE_CLICKABLE:_("clickable"),
	STATE_EDITABLE:_("editable"),
	STATE_CHECKABLE:_("checkable"),
	STATE_DRAGGABLE:_("draggable"),
	STATE_DRAGGING:_("dragging"),
	# Translators: Reported where an object which is being dragged can be dropped.
	# This is only reported for objects which support accessible drag and drop.
	STATE_DROPTARGET:_("drop target"),
	STATE_SORTED:_("sorted"),
	STATE_SORTED_ASCENDING:_("sorted ascending"),
	STATE_SORTED_DESCENDING:_("sorted descending"),
	STATE_HASLONGDESC:"has long description",
}

negativeStateLabels={
	# Translators: This is presented when a selectable object (e.g. a list item) is not selected.
	STATE_SELECTED:_("not selected"),
	# Translators: This is presented when a checkbox is not checked.
	STATE_CHECKED:_("not checked"),
}

silentRolesOnFocus={
	ROLE_PANE,
	ROLE_ROOTPANE,
	ROLE_FRAME,
	ROLE_UNKNOWN,
	ROLE_APPLICATION,
	ROLE_TABLECELL,
	ROLE_LISTITEM,
	ROLE_MENUITEM,
	ROLE_CHECKMENUITEM,
	ROLE_TREEVIEWITEM,
}

silentValuesForRoles={
	ROLE_CHECKBOX,
	ROLE_RADIOBUTTON,
	ROLE_LINK,
	ROLE_MENUITEM,
	ROLE_APPLICATION,
}

#{ Output reasons
# These constants are used to specify the reason that a given piece of output was generated.
#: An object to be reported due to a focus change or similar.
REASON_FOCUS="focus"
#: An ancestor of the focus object to be reported due to a focus change or similar.
REASON_FOCUSENTERED="focusEntered"
#: An item under the mouse.
REASON_MOUSE="mouse"
#: A response to a user query.
REASON_QUERY="query"
#: Reporting a change to an object.
REASON_CHANGE="change"
#: A generic, screen reader specific message.
REASON_MESSAGE="message"
#: Text reported as part of a say all.
REASON_SAYALL="sayAll"
#: Content reported due to caret movement or similar.
REASON_CARET="caret"
#: No output, but any state should be cached as if output had occurred.
REASON_ONLYCACHE="onlyCache"
#}

def processPositiveStates(role, states, reason, positiveStates):
	positiveStates = positiveStates.copy()
	# The user never cares about certain states.
	if role==ROLE_EDITABLETEXT:
		positiveStates.discard(STATE_EDITABLE)
	if role!=ROLE_LINK:
		positiveStates.discard(STATE_VISITED)
	positiveStates.discard(STATE_SELECTABLE)
	positiveStates.discard(STATE_FOCUSABLE)
	positiveStates.discard(STATE_CHECKABLE)
	if STATE_DRAGGING in positiveStates:
		# It's obvious that the control is draggable if it's being dragged.
		positiveStates.discard(STATE_DRAGGABLE)
	if role == ROLE_COMBOBOX:
		# Combo boxes inherently have a popup, so don't report it.
		positiveStates.discard(STATE_HASPOPUP)
	if role in (ROLE_LINK, ROLE_BUTTON, ROLE_CHECKBOX, ROLE_RADIOBUTTON, ROLE_TOGGLEBUTTON, ROLE_MENUITEM, ROLE_TAB, ROLE_SLIDER, ROLE_DOCUMENT):
		# This control is clearly clickable according to its role
		# or reporting clickable just isn't useful.
		positiveStates.discard(STATE_CLICKABLE)
	if reason == REASON_QUERY:
		return positiveStates
	positiveStates.discard(STATE_DEFUNCT)
	positiveStates.discard(STATE_MODAL)
	positiveStates.discard(STATE_FOCUSED)
	positiveStates.discard(STATE_OFFSCREEN)
	positiveStates.discard(STATE_INVISIBLE)
	if reason != REASON_CHANGE:
		positiveStates.discard(STATE_LINKED)
		if role in (ROLE_LISTITEM, ROLE_TREEVIEWITEM, ROLE_MENUITEM, ROLE_TABLEROW) and STATE_SELECTABLE in states:
			positiveStates.discard(STATE_SELECTED)
	if role != ROLE_EDITABLETEXT:
		positiveStates.discard(STATE_READONLY)
	if role == ROLE_CHECKBOX:
		positiveStates.discard(STATE_PRESSED)
	if role == ROLE_MENUITEM:
		# The user doesn't usually care if a menu item is expanded or collapsed.
		positiveStates.discard(STATE_COLLAPSED)
		positiveStates.discard(STATE_EXPANDED)
	return positiveStates

def processNegativeStates(role, states, reason, negativeStates):
	speakNegatives = set()
	# Add the negative selected state if the control is selectable,
	# but only if it is either focused or this is something other than a change event.
	# The condition stops "not selected" from being spoken in some broken controls
	# when the state change for the previous focus is issued before the focus change.
	if role in (ROLE_LISTITEM, ROLE_TREEVIEWITEM, ROLE_TABLEROW) and STATE_SELECTABLE in states and (reason != REASON_CHANGE or STATE_FOCUSED in states):
		speakNegatives.add(STATE_SELECTED)
	# Restrict "not checked" in a similar way to "not selected".
	if (role in (ROLE_CHECKBOX, ROLE_RADIOBUTTON, ROLE_CHECKMENUITEM) or STATE_CHECKABLE in states)  and (STATE_HALFCHECKED not in states) and (reason != REASON_CHANGE or STATE_FOCUSED in states):
		speakNegatives.add(STATE_CHECKED)
	if reason == REASON_CHANGE:
		# We want to speak this state only if it is changing to negative.
		speakNegatives.add(STATE_DROPTARGET)
		# We were given states which have changed to negative.
		# Return only those supplied negative states which should be spoken;
		# i.e. the states in both sets.
		speakNegatives &= negativeStates
		if STATES_SORTED & negativeStates and not STATES_SORTED & states:
			# If the object has just stopped being sorted, just report not sorted.
			# The user doesn't care how it was sorted before.
			speakNegatives.add(STATE_SORTED)
		return speakNegatives
	else:
		# This is not a state change; only positive states were supplied.
		# Return all negative states which should be spoken, excluding the positive states.
		return speakNegatives - states
