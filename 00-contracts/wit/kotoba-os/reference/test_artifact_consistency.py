"""Cross-artifact drift guard (ADR-2606031600).

The kotoba:os contract is expressed three times — the WIT package, the genesis
JSON Schema, and the Rust `kotoba-os-types` enums. They MUST agree on the set of
device/world interfaces and the set of worlds, or a future edit silently desyncs
them (e.g. add an interface to the WIT but forget the schema's capability enum,
quietly breaking capability scoping). This test parses all three and asserts they
list the same names. Pure stdlib.

Run: `python3 -m unittest test_artifact_consistency -v`
"""

import json
import pathlib
import re
import unittest

_HERE = pathlib.Path(__file__).resolve().parent
_WIT = _HERE.parent / "kotoba-os.wit"
_SCHEMA = _HERE.parent.parent.parent / "schemas" / "kotoba-os-genesis-manifest.schema.json"
_RUST = _HERE / "kotoba-os-types" / "src" / "lib.rs"


def _pascal_to_kebab(name: str) -> str:
    parts = re.findall(r"[A-Z][a-z0-9]*", name)
    return "-".join(p.lower() for p in parts)


def _wit_names():
    txt = _WIT.read_text()
    interfaces = set(re.findall(r"^interface ([a-z0-9-]+) \{", txt, re.M))
    worlds = set(re.findall(r"^world ([a-z0-9-]+) \{", txt, re.M))
    return interfaces, worlds


def _schema_names():
    s = json.loads(_SCHEMA.read_text())
    interfaces = set(s["$defs"]["witInterface"]["enum"])
    worlds = set(s["properties"]["userland"]["items"]["properties"]["world"]["enum"])
    return interfaces, worlds


def _rust_enum_variants(enum_name: str):
    txt = _RUST.read_text()
    m = re.search(r"pub enum " + enum_name + r"\s*\{(.*?)\}", txt, re.S)
    assert m, f"enum {enum_name} not found in lib.rs"
    body = m.group(1)
    # variant idents are the PascalCase tokens at the start of a line (skip serde attrs/comments)
    variants = re.findall(r"^\s*([A-Z][A-Za-z0-9]*),", body, re.M)
    return {_pascal_to_kebab(v) for v in variants}


class ArtifactConsistency(unittest.TestCase):

    def test_wit_matches_schema_interfaces(self):
        wit_if, _ = _wit_names()
        schema_if, _ = _schema_names()
        self.assertEqual(wit_if, schema_if,
                         msg=f"WIT vs schema interface drift: {wit_if ^ schema_if}")

    def test_wit_matches_schema_worlds(self):
        _, wit_w = _wit_names()
        _, schema_w = _schema_names()
        self.assertEqual(wit_w, schema_w,
                         msg=f"WIT vs schema world drift: {wit_w ^ schema_w}")

    def test_wit_matches_rust_interfaces(self):
        wit_if, _ = _wit_names()
        rust_if = _rust_enum_variants("WitInterface")
        self.assertEqual(wit_if, rust_if,
                         msg=f"WIT vs Rust WitInterface drift: {wit_if ^ rust_if}")

    def test_wit_matches_rust_worlds(self):
        _, wit_w = _wit_names()
        rust_w = _rust_enum_variants("World")
        self.assertEqual(wit_w, rust_w,
                         msg=f"WIT vs Rust World drift: {wit_w ^ rust_w}")

    def test_expected_baseline_is_present(self):
        # anchor: the known R0 set, so a wholesale rename in all three at once
        # (which the pairwise checks would miss) still trips this.
        wit_if, wit_w = _wit_names()
        self.assertEqual(wit_if, {
            "io-digital", "io-analog", "io-gpio",
            "fieldbus-modbus", "fieldbus-opcua", "fieldbus-ethercat", "fieldbus-canopen",
            "datom",
        })
        self.assertEqual(wit_w, {"plc-control", "mesh-agent"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
