"""Schema coverage for the kotoba-os genesis manifest (ADR-2606031600 §D1).

Validates the positive fixture against the schema and asserts the negative
fixture is rejected for the RIGHT reasons (C3/N5 no-server-key, N3 no live
actuation at R0). Skips cleanly if `jsonschema` is absent.

Run: `python3 -m unittest test_genesis_manifest_schema -v`
"""

import json
import pathlib
import unittest

_HERE = pathlib.Path(__file__).resolve().parent
_SCHEMA = _HERE.parent.parent.parent / "schemas" / "kotoba-os-genesis-manifest.schema.json"
_EX = _HERE / "examples"

try:
    from jsonschema import Draft202012Validator
    _HAVE = True
except Exception:  # pragma: no cover
    _HAVE = False


def _load(p):
    return json.loads(pathlib.Path(p).read_text())


@unittest.skipUnless(_HAVE, "jsonschema not installed")
class GenesisManifestSchema(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.schema = _load(_SCHEMA)
        Draft202012Validator.check_schema(cls.schema)  # the schema itself is valid
        cls.validator = Draft202012Validator(cls.schema)

    def test_valid_hikari_manifest_passes(self):
        inst = _load(_EX / "genesis-hikari-pv-controller.json")
        errors = sorted(self.validator.iter_errors(inst), key=lambda e: list(e.path))
        self.assertEqual(errors, [], msg=f"unexpected: {[e.message for e in errors]}")

    def test_invalid_manifest_is_rejected(self):
        inst = _load(_EX / "genesis-INVALID-server-key.json")
        # _comment is an extra prop; additionalProperties:false also flags it,
        # so strip it to prove the rejection is the constitutional ones, not noise.
        inst.pop("_comment", None)
        errors = list(self.validator.iter_errors(inst))
        self.assertTrue(errors, "expected the invalid manifest to be rejected")
        paths = {tuple(e.absolute_path) for e in errors}
        # C3/N5: serverKey must be false
        self.assertIn(("identity", "serverKey"), paths, msg=f"paths={paths}")
        # N3: liveActuation must be false at R0
        self.assertIn(("safety", "liveActuation"), paths, msg=f"paths={paths}")

    def test_capabilities_reject_unknown_interface(self):
        inst = _load(_EX / "genesis-hikari-pv-controller.json")
        inst["capabilities"]["interfaces"].append("io-nonexistent")
        errors = list(self.validator.iter_errors(inst))
        self.assertTrue(errors, "unknown WIT interface must be rejected (capability scoping)")


if __name__ == "__main__":
    unittest.main(verbosity=2)
