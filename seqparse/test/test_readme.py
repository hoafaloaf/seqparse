"""The Python examples in README.md must match what the code does."""

import doctest
import os
import pathlib
import re
import tempfile
import unittest

README = pathlib.Path(__file__).resolve().parents[2] / "README.md"


def _examples():
    """The README's ```pycon blocks, in order."""
    return re.findall(r"```pycon\n(.*?)```", README.read_text(), re.S)


def _run(example):
    """Run one example as a doctest; return (failures, report)."""
    test = doctest.DocTestParser().get_doctest(example, {}, "README", None, 0)
    report = []
    runner = doctest.DocTestRunner(optionflags=doctest.ELLIPSIS)
    runner.run(test, out=report.append)
    return runner.failures, "".join(report)


@unittest.skipUnless(
    README.exists(), "README.md is not shipped with the package"
)
class TestReadmeExamples(unittest.TestCase):
    """Doctest every Python example in the README."""

    def test_there_are_examples(self):
        """The examples are found (guards the regex)."""
        self.assertEqual(len(_examples()), 2)

    @unittest.skipIf(os.sep != "/", "the example shows POSIX paths")
    def test_scan_example(self):
        """The Seqparse walkthrough, against the file tree it describes."""
        names = ["0001", "0002", "0003", "0004", "0010"]
        with tempfile.TemporaryDirectory() as root:
            os.mkdir(os.path.join(root, "test_dir"))
            for name in [f"TEST_DIR.{n}.tif" for n in names] + [
                "SINGLETON.jpg"
            ]:
                pathlib.Path(root, "test_dir", name).touch()
            cwd = os.getcwd()
            os.chdir(root)
            try:
                failures, report = _run(_examples()[0])
            finally:
                os.chdir(cwd)
        self.assertEqual(failures, 0, report)

    def test_sequence_example(self):
        """The FrameSequence example."""
        failures, report = _run(_examples()[1])
        self.assertEqual(failures, 0, report)
