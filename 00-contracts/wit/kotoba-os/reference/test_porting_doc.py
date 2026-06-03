"""Keep the porting handoff (../PORTING.md) honest (ADR-2606031600).

PORTING.md maps each reference artifact to its production target in the
40-engine/kotoba subrepo. This test checks the doc stays grounded: every
reference artifact it names actually exists here, and it names the real port
targets + the run-all gate. Pure stdlib.

Run: `python3 -m unittest test_porting_doc -v`
"""

import pathlib
import unittest

_HERE = pathlib.Path(__file__).resolve().parent
_DOC = _HERE.parent / "PORTING.md"
_KOTOBA_OS = _HERE.parent  # 00-contracts/wit/kotoba-os


class PortingDoc(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.text = _DOC.read_text()

    def test_doc_exists_and_links_the_adr(self):
        self.assertTrue(_DOC.exists())
        self.assertIn("ADR-2606031600", self.text)

    def test_names_every_real_reference_artifact(self):
        # the artifacts the doc maps FROM must exist on disk
        for art in [
            "kotoba-os.wit",
            "kotoba-os-types",
            "plc-host-runner",
            "mesh.rs",
            "cid.rs",
        ]:
            self.assertIn(art, self.text, msg=f"{art} not mentioned in PORTING.md")
        # and each named reference dir/file actually exists
        for rel in [
            "kotoba-os.wit",
            "reference/kotoba-os-types",
            "reference/plc-host-runner",
            "reference/kotoba-os-types/src/mesh.rs",
            "reference/kotoba-os-types/src/cid.rs",
        ]:
            self.assertTrue((_KOTOBA_OS / rel).exists(), msg=f"missing artifact {rel}")

    def test_names_real_port_target_crates(self):
        # the production crates it maps TO are real kotoba crates
        for crate in ["kotoba-core", "kotoba-kqe", "kotoba-dht", "kotoba-runtime"]:
            self.assertIn(crate, self.text)

    def test_references_the_acceptance_gate(self):
        self.assertIn("run-all.sh", self.text)

    def test_lists_constitutional_invariants(self):
        # the non-goals the production crate must preserve
        for n in ["N1", "N3", "N4", "N5", "N7"]:
            self.assertIn(n, self.text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
