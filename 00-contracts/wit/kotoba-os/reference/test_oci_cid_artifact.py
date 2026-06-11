"""Coverage for the kotoba-os OCI-CID artifact convention (ADR-2606031600 §D4).

The artifact's core invariant is that the OCI manifest sha2-256 `digest` and the
`cid` are the SAME hash re-encoded: cid = multibase-base32(0x01 0x55 0x12 0x20 ||
digest). This test DECODES the cid back to a digest (via stdlib base64.b32decode —
independent of any encoder) and asserts it equals the `digest` field. That makes
"digest = CID" a checkable equivalence, not a slogan. Plus: the image is pulled
from IPFS only (no commercial registry), and schema-validates.

Run: `python3 -m unittest test_oci_cid_artifact -v`
"""

import base64
import json
import pathlib
import unittest

_HERE = pathlib.Path(__file__).resolve().parent
_SCHEMA = _HERE.parent.parent.parent / "schemas" / "kotoba-os-oci-artifact.schema.json"
_EX = _HERE / "examples" / "oci-artifact-plc-unikernel.json"

try:
    from jsonschema import Draft202012Validator
    _HAVE_JS = True
except Exception:  # pragma: no cover
    _HAVE_JS = False

# commercial registries the §D4 convention forbids
_FORBIDDEN_REGISTRIES = ("docker.io", "ghcr.io", "quay.io", "registry-1.docker.io",
                         "gcr.io", "public.ecr.aws")


def _load(p):
    return json.loads(pathlib.Path(p).read_text())


def cid_to_sha256_hex(cid: str) -> str:
    """Decode a CIDv1(raw, sha2-256) multibase-base32 string back to its 32-byte
    sha2-256 digest (hex). Uses stdlib b32decode as the trusted inverse."""
    assert cid.startswith("b"), "expected base32 multibase ('b' prefix)"
    body = cid[1:]
    pad = "=" * ((8 - len(body) % 8) % 8)
    raw = base64.b32decode(body.upper() + pad)
    assert raw[0] == 0x01, "not CIDv1"
    assert raw[1] == 0x55, "not raw codec (0x55)"
    assert raw[2] == 0x12, "not sha2-256 multihash (0x12)"
    assert raw[3] == 0x20, "multihash length != 32"
    return raw[4:4 + 32].hex()


class OciCidArtifact(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.a = _load(_EX)

    def test_digest_equals_cid_the_real_invariant(self):
        digest_hex = self.a["digest"].split(":", 1)[1]
        self.assertEqual(
            cid_to_sha256_hex(self.a["cid"]), digest_hex,
            msg="cid does not decode to the OCI manifest digest — equivalence broken",
        )

    def test_imageref_is_ipfs_and_carries_the_cid(self):
        ref = self.a["imageRef"]
        self.assertTrue(ref.startswith("ipfs://"), "imageRef must be ipfs://")
        self.assertTrue(ref.endswith(self.a["cid"]), "imageRef must carry the cid")

    def test_no_commercial_registry_anywhere(self):
        blob = json.dumps(self.a).lower()
        for reg in _FORBIDDEN_REGISTRIES:
            self.assertNotIn(reg, blob, msg=f"commercial registry {reg} present")

    def test_pull_is_ipfs_only(self):
        self.assertEqual(self.a["pull"]["type"], "ipfs")
        self.assertGreaterEqual(len(self.a["pull"]["gateways"]), 1)

    def test_runtime_class_is_allowed(self):
        self.assertIn(self.a["runtimeClass"],
                      {"microvm-firecracker", "microvm-uhyve", "microvm-kata", "runwasi"})

    def test_placement_is_murakumo(self):
        self.assertEqual(self.a["placement"]["kubelet"], "murakumo")

    @unittest.skipUnless(_HAVE_JS, "jsonschema not installed")
    def test_schema_validates(self):
        schema = _load(_SCHEMA)
        Draft202012Validator.check_schema(schema)
        errors = list(Draft202012Validator(schema).iter_errors(self.a))
        self.assertEqual(errors, [], msg=f"{[e.message for e in errors]}")

    @unittest.skipUnless(_HAVE_JS, "jsonschema not installed")
    def test_schema_rejects_a_registry_ref(self):
        schema = _load(_SCHEMA)
        bad = dict(self.a)
        bad["imageRef"] = "ghcr.io/etzhayyim/kotoba-os:r0"  # commercial registry tag
        errors = list(Draft202012Validator(schema).iter_errors(bad))
        self.assertTrue(errors, "a registry imageRef must be rejected by the schema")


if __name__ == "__main__":
    unittest.main(verbosity=2)
