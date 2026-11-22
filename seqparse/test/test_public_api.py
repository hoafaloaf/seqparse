"""
The public API: each module's __all__ must be complete and accurate.

__all__ names whatever a user can pass to or receive from the library. A new
public top-level name must either be exported there or, if it is meant to be
an implementation detail, listed in INTERNAL below.
"""

import ast
import importlib
import inspect
import unittest

PUBLIC_MODULES = (
    "seqparse",
    "seqparse.cli.seqls",
    "seqparse.containers",
    "seqparse.files",
    "seqparse.regex",
    "seqparse.seqparse",
    "seqparse.sequences",
)

# Public-looking names that are deliberately not part of the API.
INTERNAL = {
    "seqparse": {"restore_slots"},
    "seqparse.seqparse": {"PathLike"},
    "seqparse.sequences": {"FrameStore", "Frames"},
}


def _defined_names(module):
    """Names a module defines at the top level (imports excluded)."""
    names = set()
    for node in ast.parse(inspect.getsource(module)).body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            names.update(t.id for t in node.targets if isinstance(t, ast.Name))
        elif isinstance(node, ast.AnnAssign) and isinstance(
            node.target, ast.Name
        ):
            names.add(node.target.id)
    return names


class TestAll(unittest.TestCase):
    """__all__ in every public module."""

    def test_every_module_defines_all_without_duplicates(self):
        """__all__ exists, has no repeats, and every name resolves."""
        for name in PUBLIC_MODULES:
            with self.subTest(module=name):
                module = importlib.import_module(name)
                exported = getattr(module, "__all__", None)
                self.assertIsNotNone(exported, f"{name} has no __all__")
                self.assertEqual(len(exported), len(set(exported)))
                for attr in exported:
                    self.assertTrue(hasattr(module, attr), attr)

    def test_only_names_the_module_defines_are_exported(self):
        """Imported names (Any, os, ...) must not end up in __all__."""
        for name in PUBLIC_MODULES:
            with self.subTest(module=name):
                module = importlib.import_module(name)
                stray = set(module.__all__) - _defined_names(module)
                self.assertEqual(stray, set())

    def test_every_public_name_is_exported_or_internal(self):
        """Nothing public is missing from __all__ (it went stale before)."""
        for name in PUBLIC_MODULES:
            with self.subTest(module=name):
                module = importlib.import_module(name)
                public = {
                    n for n in _defined_names(module) if not n.startswith("_")
                }
                missing = (
                    public - set(module.__all__) - INTERNAL.get(name, set())
                )
                self.assertEqual(
                    missing, set(), f"export or list as INTERNAL: {missing}"
                )

    def test_internal_list_is_not_stale(self):
        """INTERNAL only names things that exist and are not exported."""
        for name, internal in INTERNAL.items():
            with self.subTest(module=name):
                module = importlib.import_module(name)
                self.assertLessEqual(internal, _defined_names(module))
                self.assertEqual(internal & set(module.__all__), set())
