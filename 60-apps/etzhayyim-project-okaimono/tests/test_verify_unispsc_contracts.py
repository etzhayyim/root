from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
VERIFIER_PATH = ROOT / "scripts/verify_unispsc_contracts.py"


def load_verifier():
    spec = importlib.util.spec_from_file_location("verify_unispsc_contracts", VERIFIER_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class VerifyUnispscContractsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)
        self.okaimono_root = self.repo / "60-apps/etzhayyim-project-okaimono"
        self.shopping_root = self.repo / "60-apps/etzhayyim-project-shopping"
        self._write_contract_tree()
        self.verifier = load_verifier()

    def _write_contract_tree(self) -> None:
        proto_text = "\n".join([
            'syntax = "proto3";',
            "message Product {",
            "  string unispsc_code = 13;",
            "  string unispsc_segment = 14;",
            "  string unispsc_family = 15;",
            "  string unispsc_class = 16;",
            "  string commodity_did = 17;",
            "}",
            "message OrderItem {",
            "  string unispsc_code = 5;",
            "  string commodity_did = 6;",
            "}",
            "message UpsertListingRequest {",
            "  bool validate_unispsc_classification = 4;",
            "}",
            "message ImportUnispscSegmentRequest {}",
            "message ImportUnispscSegmentPlan {}",
            "service CatalogService {",
            "  rpc ImportUnispscSegment(ImportUnispscSegmentRequest) returns (ImportUnispscSegmentPlan);",
            "}",
        ])
        for root in [self.okaimono_root, self.shopping_root]:
            proto_path = root / "proto/v1/shopping.proto"
            proto_path.parent.mkdir(parents=True, exist_ok=True)
            proto_path.write_text(proto_text, encoding="utf-8")

        manifest_path = self.okaimono_root / "appview/okaimono-shopping-mcp-component/kotodama.jsonld"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps({
            "profile": {
                "capabilities": [
                    "e-commerce",
                    "product-catalog",
                    "unispsc-classification",
                    "unispsc-catalog-import",
                ],
            },
            "triggers": {
                "subscribeRepos": {
                    "collections": [
                        "com.etzhayyim.apps.okaimono.catalogItem",
                        "com.etzhayyim.apps.okaimono.order",
                        "com.etzhayyim.apps.unispsc.commodity",
                    ],
                },
            },
        }), encoding="utf-8")

        doc_text = "\n".join([
            "catalog-search-unispsc",
            "import-unispsc-segment",
            "procurement-find-offers-unispsc",
            "com.etzhayyim.apps.openUnispsc.syncCatalogItem",
            "com.etzhayyim.apps.openUnispsc.planCatalogPurchase",
        ])
        for relative in [
            "appview/okaimono-shopping-mcp-component/README.md",
            "CLAUDE.md",
            "okaimono-etzhayyim-ai-ec-operating-spec.md",
        ]:
            doc_path = self.okaimono_root / relative
            doc_path.parent.mkdir(parents=True, exist_ok=True)
            doc_path.write_text(doc_text, encoding="utf-8")

    def verify(self) -> dict:
        with (
            mock.patch.object(self.verifier, "ROOT", self.okaimono_root),
            mock.patch.object(self.verifier, "SHOPPING_ROOT", self.shopping_root),
            mock.patch.object(self.verifier.shutil, "which", return_value=None),
        ):
            return self.verifier.verify()

    def test_accepts_complete_contract_tree(self) -> None:
        result = self.verify()

        self.assertTrue(result["ok"], result)
        self.assertEqual([], result["missing"])
        self.assertTrue(result["checks"]["proto:okaimono:patterns"])
        self.assertTrue(result["checks"]["manifest:capabilities"])

    def test_fails_when_required_proto_field_is_missing(self) -> None:
        proto_path = self.okaimono_root / "proto/v1/shopping.proto"
        proto_path.write_text(
            proto_path.read_text(encoding="utf-8").replace("  string commodity_did = 17;\n", ""),
            encoding="utf-8",
        )

        result = self.verify()

        self.assertFalse(result["ok"], result)
        self.assertIn("proto:okaimono:string commodity_did = 17;", result["missing"])
        self.assertFalse(result["checks"]["proto:okaimono:patterns"])

    def test_fails_when_manifest_capability_is_missing(self) -> None:
        manifest_path = self.okaimono_root / "appview/okaimono-shopping-mcp-component/kotodama.jsonld"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["profile"]["capabilities"].remove("unispsc-catalog-import")
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

        result = self.verify()

        self.assertFalse(result["ok"], result)
        self.assertIn("manifest:capability:unispsc-catalog-import", result["missing"])
        self.assertFalse(result["checks"]["manifest:capabilities"])

    def test_fails_when_required_doc_command_is_missing(self) -> None:
        readme_path = self.okaimono_root / "appview/okaimono-shopping-mcp-component/README.md"
        readme_path.write_text(
            readme_path.read_text(encoding="utf-8").replace("import-unispsc-segment\n", ""),
            encoding="utf-8",
        )

        result = self.verify()

        self.assertFalse(result["ok"], result)
        self.assertIn("doc:readme:import-unispsc-segment", result["missing"])
        self.assertFalse(result["checks"]["doc:readme:patterns"])


if __name__ == "__main__":
    unittest.main()
