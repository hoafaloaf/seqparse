"""Every ``>>>`` example in the docstrings must show real output."""

import contextlib
import doctest
import importlib
import os
import tempfile
import unittest

MODULES = (
    "seqparse",
    "seqparse.cli.seqls",
    "seqparse.containers",
    "seqparse.files",
    "seqparse.regex",
    "seqparse.seqparse",
    "seqparse.sequences",
)

# The file structure that the Seqparse docstring describes.
TEST_DIR_FILES = (
    "TEST_DIR.0001.tif",
    "TEST_DIR.0002.tif",
    "TEST_DIR.0003.tif",
    "TEST_DIR.0004.tif",
    "TEST_DIR.0010.tif",
    "SINGLETON.jpg",
)


def _run_examples(module_name):
    """Run a module's docstring examples in a directory with test_dir."""
    module = importlib.import_module(module_name)
    runner = doctest.DocTestRunner(optionflags=doctest.ELLIPSIS)
    report = []
    with tempfile.TemporaryDirectory() as tmp:
        os.mkdir(os.path.join(tmp, "test_dir"))
        for name in TEST_DIR_FILES:
            open(os.path.join(tmp, "test_dir", name), "w").close()
        with contextlib.chdir(tmp):
            for test in doctest.DocTestFinder().find(module, module_name):
                runner.run(test, out=report.append)
    return runner.failures, "".join(report)


class TestDocstringExamples(unittest.TestCase):
    """Doctest every module, so the examples cannot drift from the code."""

    def test_modules_have_examples(self):
        """The examples are found (guards against testing nothing)."""
        total = 0
        for name in MODULES:
            module = importlib.import_module(name)
            for test in doctest.DocTestFinder().find(module, name):
                total += len(test.examples)
        self.assertGreater(total, 30)

    def test_examples_are_correct(self):
        """Each module's examples run and print what the docstring says."""
        for name in MODULES:
            with self.subTest(module=name):
                if name == "seqparse.seqparse" and os.sep != "/":
                    self.skipTest("the examples show POSIX paths")
                failures, report = _run_examples(name)
                self.assertEqual(failures, 0, report)
