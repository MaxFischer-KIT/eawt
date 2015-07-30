# #-# maintained at https://github.com/MaxFischer-KIT/eawt
"""
Tools for integrating GC with python applications

This is a standalone module.

:warning: Since an application on a remote system does not have access to the
    original repository at runtime, it is mandatory to include the relevant
    functions in your own codebase.
"""

# standard library imports
import inspect
import linecache
import sys
import ast

# third party imports
# <Standalone: No Dependencies>

# application/library imports
# <Standalone: No Dependencies>

NO_DEFAULT = object()


def gc_var_or_default(gc_var_name, default=NO_DEFAULT, gc_var_str="@", var_type=ast.literal_eval):
    """
    Use an injected GridControl variable or fall back to a default

    This function can be used in place of any variable in the form
    ``gc_var_or_default('@MU_COUNT@', 2)``. If GC replaces the variable
    in source code (e.g. a config), the call is implicitly changed to
    ``gc_var_or_default('16', 2)`` which is detected by the function,
    yielding the new input.

    :param gc_var_name: name of the variable for GC, including GC variable strings
    :type gc_var_name: str, unicode
    :param default: value to use if no replacement by GC happened
    :param gc_var_str: the start/end string of GC the variable (e.g. ``"@"``)
    :type gc_var_str: str, unicode
    :param var_type: callable to convert literal to appropriate variable type
    :type var_type: callable

    :note: If var_type is ``None``, it is automatically guessed using
        ``type(default)``. The reverse does not hold true; if ``var_type`` is
        explicitly specified, ``default`` is not checked for type compatibility.

    :note: By convention from GC, gc_var_str should be ``"@"`` or ``"__"``. This
        is not enforced by the function.
    """
    if gc_var_name.startswith(gc_var_str) and gc_var_name.endswith(gc_var_str):
        if default is NO_DEFAULT:
            raise TypeError("'%s' must be a GC variable/parameter (no default given as fallback)" % gc_var_name.strip(gc_var_str))
        return default
    var_type = type(default) if var_type is None else var_type
    return var_type(gc_var_name)

def gc_var_or_callable_parameter(gc_var_name, callable, gc_var_str="@", var_type=ast.literal_eval):
    """
    Similar to :py:func:`~.gc_var_or_default`, extracting the default
    dynamically from a callable

    This function inspects the callstack to deduct what parameter of ``callable``
    its result is assigned to. It is ideally used as follows::

        def foo_func(an_arg, another_arg=2, foobarme="Yes"):
            print an_arg, another_arg, foobarme

        foo_func(
            1,
            another_arg = gc_var_or_callable_parameter('@MY_GC_ARG@', callable=foo_func),
            foobarme = gc_var_or_callable_parameter('@FOOS_GC_ARG@', callable=foo_func),
            )

    :note: If the type of the variable should also be guessed, ``var_type`` must
           be set to ``None``.

    :warning: This function performs its lookup by inspecting source code from
              the call frame. This has some limitations:

              1. There may be only one call to ``gc_var_or_callable_parameter``
                 per line of source code. Repeated use on multiple lines is fine,
                 even in nested scopes.

              2. There may be no equal sign ``=`` (as a string, syntactic element,
                 etc.) between the equal sign assigning this function to
                 ``callable``\ s parameter.

              3. If the function is bound to another name (e.g. via
                 ``from X import Y as Z``) then only the name in the closest
                 scope (local, global, module) may be used.
    """
    # extract callable signature
    args, _, _, defaults = inspect.getargspec(callable)
    # extract the variable name from the callstack:
    #  1. Look at the frame calling this function
    #  2. Guess the name this function is bound to
    #  3. Read the source code where this function is called
    #  4. Backtrack the source code until the function is called by name
    #  5. Backtrack the source code until an assignment via ``=`` is done
    #  6. Set the first non-whitespace character sequence as the parameter name
    call_frame = sys._getframe(1)
    try:
        self_name = [lcl for lcl in call_frame.f_locals if call_frame.f_locals[lcl] is gc_var_or_callable_parameter][0]
    except IndexError:
        try:
            self_name = [gbl for gbl in call_frame.f_globals if call_frame.f_globals[gbl] is gc_var_or_callable_parameter][0]
        except IndexError:
            self_name = gc_var_or_callable_parameter.__name__
    self_called = False
    var_assigned = False
    # variable assignment and name might be on different lines, so backtrack a little if needed
    for backtrack in range(8):
        # always ignore comments
        call_line = linecache.getline(call_frame.f_code.co_filename, call_frame.f_lineno-backtrack).partition("#")[0].strip()
        # variable name we are assigned to must be before our name
        if self_name in call_line:
            self_called = True
            call_line = call_line.partition(self_name)[0].strip()
        # variable name is always before assignment operator, fast forward there
        if self_called and "=" in call_line:
            var_assigned = True
            call_line = call_line.rpartition("=")[0].strip()
        # variable name is the next name
        if var_assigned and call_line:
            var_name = call_line.rsplit(None, 1)[-1].strip("()")
            break
    else:
        raise ValueError("GC Tools failed to find variable name in calling frame")
    try:
        return gc_var_or_default(
            gc_var_name,
            default=defaults[args.index(var_name)-len(args)],
            gc_var_str=gc_var_str,
            var_type=var_type
        )
    except IndexError:
        # parameter BEFORE defaulting ones -> no default
        return gc_var_or_default(
            gc_var_name,
            gc_var_str=gc_var_str,
            var_type=var_type
        )

