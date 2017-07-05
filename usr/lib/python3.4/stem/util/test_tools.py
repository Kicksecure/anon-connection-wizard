# Copyright 2014, Damian Johnson and The Tor Project
# See LICENSE for licensing information

"""
Helper functions for testing.

.. versionadded:: 1.2.0

::

  clean_orphaned_pyc - delete *.pyc files without corresponding *.py

  is_pyflakes_available - checks if pyflakes is available
  is_pep8_available - checks if pep8 is available

  get_stylistic_issues - checks for PEP8 and other stylistic issues
  get_pyflakes_issues - static checks for problems via pyflakes
"""

import os
import re

import stem.util.conf
import stem.util.system

CONFIG = stem.util.conf.config_dict('test', {
  'pep8.ignore': [],
  'pyflakes.ignore': [],
  'exclude_paths': [],
})


def clean_orphaned_pyc(paths):
  """
  Deletes any file with a *.pyc extention without a corresponding *.py. This
  helps to address a common gotcha when deleting python files...

  * You delete module 'foo.py' and run the tests to ensure that you haven't
    broken anything. They pass, however there *are* still some 'import foo'
    statements that still work because the bytecode (foo.pyc) is still around.

  * You push your change.

  * Another developer clones our repository and is confused because we have a
    bunch of ImportErrors.

  :param list paths: paths to search for orphaned pyc files

  :returns: list of absolute paths that were deleted
  """

  orphaned_pyc = []

  for path in paths:
    for pyc_path in stem.util.system.files_with_suffix(path, '.pyc'):
      # If we're running python 3 then the *.pyc files are no longer bundled
      # with the *.py. Rather, they're in a __pycache__ directory.

      # TODO: At the moment there's no point in checking for orphaned bytecode
      # with python 3 because it's an exported copy of the python 2 codebase,
      # so skipping. However, we might want to address this for other callers.

      if '__pycache__' in pyc_path:
        continue

      if not os.path.exists(pyc_path[:-1]):
        orphaned_pyc.append(pyc_path)
        os.remove(pyc_path)

  return orphaned_pyc


def is_pyflakes_available():
  """
  Checks if pyflakes is availalbe.

  :returns: **True** if we can use pyflakes and **False** otherwise
  """

  try:
    import pyflakes.api
    import pyflakes.reporter
    return True
  except ImportError:
    return False


def is_pep8_available():
  """
  Checks if pep8 is availalbe.

  :returns: **True** if we can use pep8 and **False** otherwise
  """

  try:
    import pep8

    if not hasattr(pep8, 'BaseReport'):
      raise ImportError()

    return True
  except ImportError:
    return False


def get_stylistic_issues(paths, check_two_space_indents = False, check_newlines = False, check_trailing_whitespace = False, check_exception_keyword = False):
  """
  Checks for stylistic issues that are an issue according to the parts of PEP8
  we conform to. You can suppress PEP8 issues by making a 'test' configuration
  that sets 'pep8.ignore'.

  For example, with a 'test/settings.cfg' of...

  ::

    # PEP8 compliance issues that we're ignoreing...
    #
    # * E111 and E121 four space indentations
    # * E501 line is over 79 characters

    pep8.ignore E111
    pep8.ignore E121
    pep8.ignore E501

  ... you can then run tests with...

  ::

    import stem.util.conf

    test_config = stem.util.conf.get_config('test')
    test_config.load('test/settings.cfg')

    issues = get_stylistic_issues('my_project')

  If a 'exclude_paths' was set in our test config then we exclude any absolute
  paths matching those regexes.

  :param list paths: paths to search for stylistic issues
  :param bool check_two_space_indents: check for two space indentations and
    that no tabs snuck in
  :param bool check_newlines: check that we have standard newlines (\\n), not
    windows (\\r\\n) nor classic mac (\\r)
  :param bool check_trailing_whitespace: check that our lines don't end with
    trailing whitespace
  :param bool check_exception_keyword: checks that we're using 'as' for
    exceptions rather than a comma

  :returns: **dict** of the form ``path => [(line_number, message)...]``
  """

  issues = {}

  if is_pep8_available():
    import pep8

    class StyleReport(pep8.BaseReport):
      def __init__(self, options):
        super(StyleReport, self).__init__(options)

      def error(self, line_number, offset, text, check):
        code = super(StyleReport, self).error(line_number, offset, text, check)

        if code:
          issues.setdefault(self.filename, []).append((offset + line_number, '%s %s' % (code, text)))

    style_checker = pep8.StyleGuide(ignore = CONFIG['pep8.ignore'], reporter = StyleReport)
    style_checker.check_files(list(_python_files(paths)))

  if check_two_space_indents or check_newlines or check_trailing_whitespace or check_exception_keyword:
    for path in _python_files(paths):
      with open(path) as f:
        file_contents = f.read()

      lines, prev_indent = file_contents.split('\n'), 0
      is_block_comment = False

      for index, line in enumerate(lines):
        whitespace, content = re.match('^(\s*)(.*)$', line).groups()

        # TODO: This does not check that block indentations are two spaces
        # because differentiating source from string blocks ("""foo""") is more
        # of a pita than I want to deal with right now.

        if '"""' in content:
          is_block_comment = not is_block_comment

        if check_two_space_indents and '\t' in whitespace:
          issues.setdefault(path, []).append((index + 1, 'indentation has a tab'))
        elif check_newlines and '\r' in content:
          issues.setdefault(path, []).append((index + 1, 'contains a windows newline'))
        elif check_trailing_whitespace and content != content.rstrip():
          issues.setdefault(path, []).append((index + 1, 'line has trailing whitespace'))
        elif check_exception_keyword and content.lstrip().startswith('except') and content.endswith(', exc:'):
          # Python 2.6 - 2.7 supports two forms for exceptions...
          #
          #   except ValueError, exc:
          #   except ValueError as exc:
          #
          # The former is the old method and no longer supported in python 3
          # going forward.

          # TODO: This check only works if the exception variable is called
          # 'exc'. We should generalize this via a regex so other names work
          # too.

          issues.setdefault(path, []).append((index + 1, "except clause should use 'as', not comma"))

  return issues


def get_pyflakes_issues(paths):
  """
  Performs static checks via pyflakes. False positives can be ignored via
  'pyflakes.ignore' entries in our 'test' config. For instance...

  ::

    pyflakes.ignore stem/util/test_tools.py => 'pyflakes' imported but unused
    pyflakes.ignore stem/util/test_tools.py => 'pep8' imported but unused

  If a 'exclude_paths' was set in our test config then we exclude any absolute
  paths matching those regexes.

  :param list paths: paths to search for problems

  :returns: dict of the form ``path => [(line_number, message)...]``
  """

  issues = {}

  if is_pyflakes_available():
    import pyflakes.api
    import pyflakes.reporter

    class Reporter(pyflakes.reporter.Reporter):
      def __init__(self):
        self._ignored_issues = {}

        for line in CONFIG['pyflakes.ignore']:
          path, issue = line.split('=>')
          self._ignored_issues.setdefault(path.strip(), []).append(issue.strip())

      def unexpectedError(self, filename, msg):
        self._register_issue(filename, None, msg)

      def syntaxError(self, filename, msg, lineno, offset, text):
        self._register_issue(filename, lineno, msg)

      def flake(self, msg):
        self._register_issue(msg.filename, msg.lineno, msg.message % msg.message_args)

      def _is_ignored(self, path, issue):
        # Paths in pyflakes_ignore are relative, so we need to check to see if our
        # path ends with any of them.

        for ignored_path, ignored_issues in list(self._ignored_issues.items()):
          if path.endswith(ignored_path) and issue in ignored_issues:
            return True

        return False

      def _register_issue(self, path, line_number, issue):
        if not self._is_ignored(path, issue):
          issues.setdefault(path, []).append((line_number, issue))

    reporter = Reporter()

    for path in _python_files(paths):
      pyflakes.api.checkPath(path, reporter)

  return issues


def _python_files(paths):
  for path in paths:
    for file_path in stem.util.system.files_with_suffix(path, '.py'):
      skip = False

      for exclude_path in CONFIG['exclude_paths']:
        if re.match(exclude_path, file_path):
          skip = True
          break

      if not skip:
        yield file_path
