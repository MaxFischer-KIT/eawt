import os
try:
	# ANSI support on windows
	import colorama
except ImportError:
	colorama = None
	_winANSIsupport = False
else:
	colorama.init()
	_winANSIsupport = True

"""
module textmode

Provides modificators for output streams to modify the appearance, such as
adding color or writing bold.
"""

__all__ = ['COLORS','Colors','colors','TONE','BACK','MODE']

COLORS = Colors = colors = ('Black', 'Red', 'Green', 'Orange', 'Blue', 'Magenta', 'Cyan', 'White', 'Default')

# ANSI SGR codes
def getANSISGR(*nums):
	return ( "\x1b[" + ("%d;"*len(nums))[:-1] + "m") % tuple(nums)

def _ansi_setCursorPos(x = 0, y = 0):
	return "\x1b[%d;%dH"%(x,y)

def _ansi_clearScreen():
	return "\x1b[2J"

class _ansi_TONE(object):
	base = 30

class _ansi_BACK(object):
	base = 40

for num, name in enumerate(colors):
	for obj in (_ansi_TONE, _ansi_BACK):
		setattr(obj, name, getANSISGR(obj.base+num))
		setattr(obj, name.lower(), getANSISGR(obj.base+num))
		setattr(obj, name.upper(), getANSISGR(obj.base+num))

class _ansi_MODE(object):
	CLEAR = Clear = clear = RESET = Reset = reset = getANSISGR(0)
	BOLD  = Bold  = bold  = getANSISGR(1)
	FAINT = Faint = faint = getANSISGR(2)
	CURSIVE = Cursive = cursive = ITALIC = Italic = italic = getANSISGR(3)
	UNDERLINE = Underline = underline = getANSISGR(4)
	BLINK = Blink = blink = getANSISGR(5)
	FLASH = Flash = flash = getANSISGR(6)
	NEGATIVE = Negative = negative = INVERT = Invert = invert = getANSISGR(7)
	HIDE  = Hide = hide  = getANSISGR(8)
	SLASHED = Slashed = slashed = CROSSED = Crossed = crossed = getANSISGR(9)

# no-op dummies
def _noop_setCursorPos(x = 0, y = 0):
	return ""
def _noop_clearScreen():
	return ""
class _noop_TONE(object):
	pass
class _noop_BACK(object):
	pass
for name in colors:
	for obj in (_noop_TONE, _noop_BACK):
		setattr(obj, name, '')
		setattr(obj, name.lower(), '')
		setattr(obj, name.upper(), '')
class _noop_MODE(object):
	CLEAR = Clear = clear = RESET = Reset = reset = ''
	BOLD  = Bold  = bold  = ''
	FAINT = Faint = faint = ''
	CURSIVE = Cursive = cursive = ITALIC = Italic = italic = ''
	UNDERLINE = Underline = underline = ''
	BLINK = Blink = blink = ''
	FLASH = Flash = flash = ''
	NEGATIVE = Negative = negative = INVERT = Invert = invert = ''
	HIDE  = Hide  = hide  = ''
	SLASHED = Slashed = slashed = CROSSED = Crossed = crossed = ''

def disable():
	global setCursorPos
	global clearScreen
	global TONE
	global BACK
	global MODE
	setCursorPos = _noop_setCursorPos
	clearScreen  = _noop_clearScreen
	TONE = _noop_TONE
	BACK = _noop_BACK
	MODE = _noop_MODE

def enable(type = 'ANSI'):
	if type.upper() == 'ANSI':
		global setCursorPos
		global clearScreen
		global TONE
		global BACK
		global MODE
		setCursorPos = _ansi_setCursorPos
		clearScreen  = _ansi_clearScreen
		TONE = _ansi_TONE
		BACK = _ansi_BACK
		MODE = _ansi_MODE
	else:
		disable()

if os.name in [ 'posix', 'os2' ] or _winANSIsupport:
	enable(type = 'ANSI')
else:
	disable()