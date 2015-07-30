import unittest
import standalone.gc_tools

class Test_gc_var_or_callable_parameter(unittest.TestCase):
	def setUp(self):
		def test_parameter(strarg="str", intarg=123, fltarg=2.0):
			return {"strarg": strarg, "intarg": intarg, "fltarg": fltarg}
		self.test_parameter = test_parameter

	def test_multiline_default(self):
		result = self.test_parameter(
			strarg=standalone.gc_tools.gc_var_or_callable_parameter("@STRARG@", callable=self.test_parameter),
			intarg=standalone.gc_tools.gc_var_or_callable_parameter("@INTARG@", callable=self.test_parameter),
			fltarg=standalone.gc_tools.gc_var_or_callable_parameter("@FLTARG@", callable=self.test_parameter),
		)
		self.assertEqual("str", result["strarg"], "default argument")
		self.assertEqual(123, result["intarg"], "default argument")
		self.assertEqual(2.0, result["fltarg"], "default argument")

	def test_multiline_overwrite(self):
		result = self.test_parameter(
			strarg=standalone.gc_tools.gc_var_or_callable_parameter('"foo"', callable=self.test_parameter),
			intarg=standalone.gc_tools.gc_var_or_callable_parameter("321", callable=self.test_parameter),
			fltarg=standalone.gc_tools.gc_var_or_callable_parameter("1.0", callable=self.test_parameter),
		)
		self.assertEqual("foo", result["strarg"], "overwritten argument")
		self.assertEqual(321, result["intarg"], "overwritten argument")
		self.assertEqual(1.0, result["fltarg"], "overwritten argument")

	def test_singleline(self):
		result = self.test_parameter(strarg="bar", intarg=standalone.gc_tools.gc_var_or_callable_parameter("321", callable=self.test_parameter), fltarg=3.0)
		self.assertEquals("bar", result["strarg"], "given argument")
		self.assertEquals(321, result["intarg"], "overwritten argument")
		self.assertEquals(3.0, result["fltarg"], "given argument")

	def test_renamed(self):
		from standalone.gc_tools import gc_var_or_callable_parameter as func_alias
		result = self.test_parameter(strarg="bar", intarg=func_alias("321", callable=self.test_parameter), fltarg=3.0)
		self.assertEquals("bar", result["strarg"], "given argument")
		self.assertEquals(321, result["intarg"], "overwritten argument")
		self.assertEquals(3.0, result["fltarg"], "given argument")