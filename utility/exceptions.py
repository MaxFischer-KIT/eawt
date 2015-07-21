"""
Provides custom Exceptions and Errors and some convenience tools to handle them.

*Exception*
  A behaviour that is not part of the regular program flow but not itself to be
  considered as 'wrong'; exceptions take the role of special signals.
  Example1: attempting a lookup with a key that is not known
  Example2: addressing a remote resource that is temporarily unavailable

*Error*
  A behaviour that is not supposed to happen or be attempted.
  Example1: attempting a lookup with a key that is not valid
  Example2: addressing a remote resource that does not exist
"""

# core modules
import sys
import logging
import linecache

# advanced modules

# custom modules
from . import textmode

logging.basicConfig()

def logTraceback(exClass, exValue, traceback, logger = 'EXCEPTION'):
	logger = logging.getLogger(logger)
	# late-bind to allow disabling
	TONE, MODE = textmode.TONE, textmode.MODE
	# log traceback
	tracebackDepth = 0
	logger.critical("    .")
	if exClass is not None:
		exMessage = formatException(exClass, exValue, traceback)
		for line in exMessage.strip().splitlines():
			logger.critical('>>>>| %s%s%s%s', MODE.BOLD, TONE.RED, line, MODE.RESET)
		logger.critical('    | =====================================')
	while traceback:
		logger.critical("    .")
		tracebackDepth +=1
		exCode = traceback.tb_frame.f_code
		linecache.checkcache(exCode.co_filename)
		# Exception position
		logger.critical(  '____|%s%s%s Traceback #%02d %-20s [%s:%03d]%s', MODE.UNDERLINE, MODE.BOLD, TONE.BLUE, tracebackDepth, "'%s'"%exCode.co_name, exCode.co_filename, traceback.tb_lineno, MODE.RESET)
		fmtLine = lambda line_no: linecache.getline(exCode.co_filename, line_no).rstrip().replace('\t', '  ')
		logger.debug(    '%03d | %s', (traceback.tb_lineno - 5), fmtLine(traceback.tb_lineno - 5))
		logger.debug(    '%03d | %s', (traceback.tb_lineno - 4), fmtLine(traceback.tb_lineno - 4))
		logger.info(     '%03d | %s', (traceback.tb_lineno - 3), fmtLine(traceback.tb_lineno - 3))
		logger.info(     '%03d | %s', (traceback.tb_lineno - 2), fmtLine(traceback.tb_lineno - 2))
		logger.error(  '%s%s%03d | %s%s', MODE.BOLD, TONE.ORANGE, (traceback.tb_lineno - 1), fmtLine(traceback.tb_lineno - 1), MODE.RESET)
		logger.critical('%s%s  =>|>%s%s', MODE.BOLD, TONE.RED, fmtLine(traceback.tb_lineno + 0), MODE.RESET)
		logger.error(  '%s%s%03d | %s%s', MODE.BOLD, TONE.ORANGE, (traceback.tb_lineno + 1), fmtLine(traceback.tb_lineno + 1), MODE.RESET)
		logger.info(     '%03d | %s', (traceback.tb_lineno + 2),fmtLine(traceback.tb_lineno + 2))
		logger.info(     '%03d | %s', (traceback.tb_lineno + 3),fmtLine(traceback.tb_lineno + 3))
		logger.debug(    '%03d | %s', (traceback.tb_lineno + 4),fmtLine(traceback.tb_lineno + 4))
		logger.debug(    '%03d | %s', (traceback.tb_lineno + 5),fmtLine(traceback.tb_lineno + 5))
		logger.critical(  '----+ ----------')
		# Output local and class variables
		def formatRepr(obj):
			try:
				objRepr = repr(obj)
				if len(objRepr) > 500:
					return objRepr[:497] + '...'
				return objRepr
			except Exception:
				return '<not representable>'
		def logVardict( varDict, prefix = '', log = logger.warning):
			maxlen = max(map(len, varDict.keys()) + [0])
			for varName in sorted(varDict.keys()):
				log('    |  %s%s = %s', prefix, varName.ljust(maxlen), formatRepr(varDict[varName]))
		localVars = dict(traceback.tb_frame.f_locals)
		localCls  = localVars.pop('self', None)
		logger.warning(    '____|%s%s Local variables     %s', MODE.UNDERLINE, MODE.BOLD, MODE.RESET)
		logVardict(localVars)
		logger.warning(    '----+ ----------')
		if localCls is not None:
			try:
				logger.warning(    '____|%s%s Class variables     (%s)%s', MODE.UNDERLINE, MODE.BOLD, formatRepr(localCls), MODE.RESET)
				classVars = {}
				if getattr(localCls, '__dict__', []): # default classes
					classVars = getattr(localCls,'__dict__', {})
				elif hasattr(localCls, '__slots__'): # signature'd classes
					logVardict({'__slots__' : getattr(localCls,'__slots__')})
					classVars = dict((name, getattr(localCls, name)) for name in getattr(localCls,'__slots__'))
				elif hasattr(localCls,'_fields '): # namedtuple
					logVardict({'_fields' : getattr(localCls,'_fields')})
					classVars = dict((name, getattr(localCls, name)) for name in getattr(localCls,'_fields'))
				logVardict(classVars)
				logger.warning(    '----+ ----------')
			except:
				logger.warning(    '    | <not representable>')
				logger.warning(    '----+ ----------')
		logger.critical("    '")
		traceback = traceback.tb_next
	if exClass is not None:
		exMessage = formatException(exClass, exValue, traceback)
		logger.critical("    .")
		logger.critical('    | =====================================')
		for line in exMessage.strip().splitlines():
			logger.critical('>>>>| %s', line)
	del traceback

def formatException(exClass = None, exValue = None, traceback = None):
	"""Format an Exception to a short description"""
	del traceback
	if exClass is not None:
		if exValue is not None:
			try:
				return '%s: %s\n' % (exClass.__name__, str.join(' ', map(str, exValue.args)))
			except AttributeError:
				return '%s: %s\n' % (exClass.__name__, str(exValue))
		return '%s\n' %  exClass.__name__

def logException(logger = 'EXCEPTION'):
	"""Log a full description of the current exception"""
	return logTraceback(*sys.exc_info(), logger = logger)

def mainExceptionFrame(mainFunction, *mainArgs, **mainKWArgs):
	"""Execute a function with full error tracing"""
	try:
		mainFunction(*mainArgs, **mainKWArgs)
	except SystemExit: # Forward SystemExit exit code
		sys.exit(sys.exc_info()[1].code)
	except:
		logException()
		sys.stderr.write(formatException(*sys.exc_info()))
		sys.exit(1)

class ExceptionFrame(object):
	"""
	Context with a full stack trace if an error occurs

	:param onExceptTerminate: allow termination of the runtime
	:type onExceptTerminate: bool
	:param logger: name of the logger handling the stack trace
	:type logger: str
	:param ignore: exceptions to ignore and pass to outer scope
	:type ignore: list[Exception] or None
	"""
	def __init__(self, onExceptTerminate = True, logger = 'EXCEPTION', ignore = None):
		self._logger = logger
		self._exit   = onExceptTerminate
		self._ignore = ignore or []
	def __enter__(self):
		return self
	def __exit__(self, eType, eValue, eTrace):
		if eType is None:                      # Nothing to see here, move along
			return True
		if eType in self._ignore:
			return False
		if self._exit and eType == SystemExit: # Forward SystemExit exit code
			sys.exit(getattr(eValue,"code",1))
		if eType == KeyboardInterrupt:         # Manual break, no error
			exMessage = formatException(eType, eValue, eTrace)
			logger = logging.getLogger(self._logger)
			logger.critical("")
			logger.critical("    .")
			logger.critical('    | =====================================')
			for line in exMessage.strip().splitlines():
				logger.critical('>>>>| %s', line)
			sys.exit(1)
		logTraceback(eType, eValue, eTrace, logger = self._logger)  # no special case, full log
		if self._exit:
			sys.exit(1)

# Basic exceptions/errors
class BasicException(Exception):
	"""Base class for all custom exceptions"""
	def __init__(self, *args, **kwargs):
		Exception.__init__(self, *args, **kwargs)
	def __str__(self):
		"""Explicit display as exception for printing"""
		return "%s: %s" % (self.__class__.__name__, Exception.__str__(self))

class BasicError(BasicException):
	"""Base class for all custom errors"""
	pass

class RethrowException(BasicException):
	"""Add additional detail to a thrown exception"""
	def __init__(self, msg, exClass = BasicException):
		prevInfo = formatException(*sys.exc_info())
		if isinstance(sys.exc_info()[1], KeyboardInterrupt):
			BasicException.__init__(self, 'KeyboardInterrupt')
		else:
			raise exClass('%s\n%s'%(msg,prevInfo))

class TodoError(BasicException):
	"""Something needs to be done here"""
	def __init__(self, description = "You are not done here! At least add a proper TODO note next time!"):
		BasicException.__init__(self, 'TODO: %s' % description)

# Core exceptions/errors
class FileNotFound(BasicError):
	"""The requested file does not exist"""
	pass

class PermissionDenied(BasicError):
	"""The requested operation is not permitted"""
	pass

class InstallationError(BasicError):
	"""Local installation is insufficient"""
	pass

class APIError(BasicError):
	"""API misuse"""
	pass

class AbstractError(APIError):
	"""Abstract implementation call"""
	def __init__(self):
		APIError.__init__(self, "%s is an abstract implementation!" % sys._getframe(1).f_code.co_name)

class DeprecatedError(APIError):
	"""Deprecated implementation call"""
	def __init__(self):
		APIError.__init__(self, "%s is a deprecated implementation!" % sys._getframe(1).f_code.co_name)

class CommunicationError(BasicException):
	"""Communication with (external) resource failed"""
	def __init__(self, resource = "<unknown>"):
		BasicException.__init__(self, "Failed communication with %s" % resource)

class ValidationError(BasicError):
	"""An operation failed due to mismatch in validation credentials"""
	pass

# Special Errors/Exceptions
# TODO: Move to corresponding modules
class BackendUnavailable(BasicException):
	"""The backend is temporarily unavailable"""
	pass

# Config exceptions/errors
class ConfigurationError(BasicError):
	"""The configuration is insufficient or conflicting"""
	pass

class ConfigKeyError(BasicError):
	"""A key requested from the config is not available"""
	def __init__(self, section = '<unknown>', key = '<unknown>'):
		BasicError.__init__(self, "[%s] '%s' is undefined!" % (section, key))

class ConfigSectionError(BasicError):
	"""A section requested from the config is not available"""
	def __init__(self, section = '<unknown>'):
		BasicError.__init__(self, "[%s] is undefined!" % section)

class ConfigValueError(BasicError):
	"""A value requested from the config is not adequate"""
	def __init__(self, section = '<unknown>', key = '<unknown>', value = '<unknown>', expected = '<unknown>' ):
		BasicError.__init__(self, "[%s] '%s' = %s required as %s" % (section, key, value, expected))

# CLI argument exceptions/errors
class ArgumentValueError(BasicError):
	"""A section requested from the config is not available"""
	def __init__(self, value = '<unknown>', descr = '', expected = ''):
		BasicError.__init__(self, "Argument '%s'%s is invalid!%s" % (
			descr,
			(value and ' (%s)' % value or ''),
			(expected and ' Expected %s' % expected or ''),
			))

