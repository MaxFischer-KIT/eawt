"""
Re-implementations of various modules, functions and classes to ensure
compatibility with older versions of the standard library.
"""

try:
	from subprocess import check_output as _check_output
except ImportError:
	from _subprocess import check_output as _check_output
	import subprocess as _subprocess
	_subprocess.check_output = _check_output