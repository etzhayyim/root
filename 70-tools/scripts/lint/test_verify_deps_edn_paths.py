"""Unit tests for verify_deps_edn_paths (pure stdlib, temp-dir sandboxed)."""

import importlib.util
import pathlib
import sys
import tempfile
import unittest

spec = importlib.util.spec_from_file_location(
    "vdep", pathlib.Path(__file__).with_name("verify_deps_edn_paths.py")
)
vdep = importlib.util.module_from_spec(spec)
sys.modules["vdep"] = vdep  # dataclasses resolve annotations via sys.modules (3.14)
spec.loader.exec_module(vdep)


def make_repo(tmp: pathlib.Path, deps_edn: str, files=(), gitmodules=""):
    (tmp / "deps.edn").write_text(deps_edn)
    if gitmodules:
        (tmp / ".gitmodules").write_text(gitmodules)
    for f in files:
        p = tmp / f
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("x")
    return tmp


class CheckPathsTest(unittest.TestCase):
    def run_checks(self, deps, files=(), gitmodules=""):
        with tempfile.TemporaryDirectory() as d:
            root = make_repo(pathlib.Path(d), deps, files, gitmodules)
            return vdep.check_paths(root / "deps.edn", root)

    def test_existing_path_ok(self):
        rs = self.run_checks('{:adrs [{:id "1" :path "a.md"} {:id "2" :path "b.md"}]}',
                             files=["a.md", "b.md"])
        self.assertTrue(all(r.exists for r in rs))
        self.assertFalse(any(r.is_drift for r in rs))

    def test_bare_missing_is_drift(self):
        rs = self.run_checks('{:adrs [{:id "1" :path "gone.md"} {:id "2" :path "x.md"}]}',
                             files=["x.md"])
        drift = [r for r in rs if r.is_drift]
        self.assertEqual([d.path for d in drift], ["gone.md"])

    def test_reserved_marker_is_accepted_missing(self):
        rs = self.run_checks('{:adrs [{:id "1" :path "future.md (reserved)"} {:id "2" :path "x.md"}]}',
                             files=["x.md"])
        self.assertFalse(any(r.is_drift for r in rs))
        self.assertEqual(sum(r.is_accepted_missing for r in rs), 1)

    def test_stale_marker_flagged_when_path_exists(self):
        rs = self.run_checks('{:adrs [{:id "1" :path "here.md (reserved)"} {:id "2" :path "x.md"}]}',
                             files=["here.md", "x.md"])
        self.assertEqual(sum(r.is_stale_marker for r in rs), 1)
        self.assertFalse(any(r.is_drift for r in rs))

    def test_submodule_path_is_unverifiable_not_drift(self):
        rs = self.run_checks(
            '{:modules [{:path "40-engine/kotoba/crates/x"} {:path "real.md"}]}',
            files=["real.md"],
            gitmodules='[submodule "kotoba"]\n\tpath = 40-engine/kotoba\n\turl = x\n',
        )
        sub = [r for r in rs if r.unverifiable == "submodule"]
        self.assertEqual([s.path for s in sub], ["40-engine/kotoba/crates/x"])
        self.assertFalse(any(r.is_drift for r in rs))

    def test_external_paths_not_drift(self):
        rs = self.run_checks(
            '{:modules [{:path "https://github.com/etzhayyim/homebrew-kotoba"}'
            ' {:path "~/Library/LaunchAgents/x.plist"} {:path "real.md"}]}',
            files=["real.md"],
        )
        self.assertEqual(sum(r.unverifiable == "external" for r in rs), 2)
        self.assertFalse(any(r.is_drift for r in rs))

    def test_configured_west_project_shape_is_unverifiable_not_drift(self):
        rs = self.run_checks(
            '{:platform {:operating_entity {:github_org_open "etzhayyim"}}'
            ' :modules [{:path "orgs/etzhayyim/com-etzhayyim-kami-apps"}'
            ' {:path "orgs/etzhayyim/com-etzhayyim-kami-apps/src/lib.cljc"}'
            ' {:path "orgs/etzhayyim/com-etzhayyim-kami-apps/"}]}'
        )
        self.assertEqual(sum(r.unverifiable == "west-project" for r in rs), 3)
        self.assertFalse(any(r.is_drift for r in rs))

    def test_unknown_or_malformed_west_project_is_drift(self):
        rs = self.run_checks(
            '{:platform {:operating_entity {:github_org_open "etzhayyim"}}'
            ' :modules [{:path "orgs/etzhayim/com-etzhayyim-typo"}'
            ' {:path "orgs/etzhayyim"}'
            ' {:path "orgs/etzhayyim/../escape"}'
            ' {:path "orgs/etzhayyim/com-etzhayyim-ok/../escape"}]}'
        )
        self.assertEqual(sum(r.is_drift for r in rs), 4)
        self.assertFalse(any(r.unverifiable == "west-project" for r in rs))

    def test_edn_canonical_counterpart_satisfies_historical_md_path(self):
        rs = self.run_checks(
            '{:adrs [{:id "1" :path "90-docs/adr/one.md"}]}',
            files=["90-docs/adr/one.edn"],
        )
        self.assertEqual(rs[0].unverifiable, "edn-canonical")
        self.assertFalse(rs[0].is_drift)

    def test_numbered_layer_moved_marker_satisfies_descendant_paths(self):
        rs = self.run_checks(
            '{:modules [{:path "40-engine/leaf"} {:path "40-engine/leaf/src/x.rs"}]}',
            files=["40-engine/leaf-MOVED.edn"],
        )
        self.assertEqual(sum(r.unverifiable == "migration-marker" for r in rs), 2)
        self.assertFalse(any(r.is_drift for r in rs))

    def test_modules_and_adrs_both_walked(self):
        rs = self.run_checks(
            '{:adrs [{:id "1" :path "a.md"} {:id "2" :path "b.md"}]'
            ' :modules [{:path "m1"} {:path "m2"}]}',
            files=["a.md", "b.md", "m1", "m2"],
        )
        self.assertEqual({r.section for r in rs}, {"adrs", "modules"})
        self.assertEqual(len(rs), 4)


class DuplicatesTest(unittest.TestCase):
    def test_duplicate_adr_ids_and_module_paths(self):
        with tempfile.TemporaryDirectory() as d:
            root = make_repo(
                pathlib.Path(d),
                '{:adrs [{:id "9" :path "a.md"} {:id "9" :path "b.md"}]'
                ' :modules [{:path "m"} {:path "m"}]}',
            )
            dups = vdep.find_duplicates(root / "deps.edn")
        self.assertIn("adrs:9", dups)
        self.assertIn("modules:m", dups)


class ReverseAuditTest(unittest.TestCase):
    def make(self, tmp, deps, adr_files):
        root = make_repo(pathlib.Path(tmp), deps)
        d = root / "90-docs/adr"
        d.mkdir(parents=True)
        for name, title in adr_files:
            (d / name).write_text(
                f'---\nid: adr-x\ntitle: "{title}"\nstatus: proposed\n---\n# x\n'
            )
        return root

    def test_detects_unregistered_adr_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make(
                tmp,
                '{:adrs [{:id "2606010001" :path "90-docs/adr/2606010001-a.md"} {:id "2606010003" :path "90-docs/adr/2606010003-c.md"}]}',
                [("2606010001-a.md", "A"), ("2606010002-b.md", "B"), ("README.md", "idx")],
            )
            (root / "90-docs/adr/2606010003-c.md").write_text("x")  # registered, exists
            un = vdep.find_unregistered_adrs(root / "deps.edn", root)
        self.assertEqual(un, ["90-docs/adr/2606010002-b.md"])

    def test_register_missing_backfills_from_front_matter(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make(
                tmp,
                '{:adrs [{:id "2606010001" :path "90-docs/adr/2606010001-a.md"} {:id "2606010009" :path "90-docs/adr/2606010009-z.md"}]}',
                [("2606010002-b.md", 'ADR-2606010002: B has \\"quotes\\" inside')],
            )
            rc = vdep.register_missing(root / "deps.edn", root)
            self.assertEqual(rc, 0)
            src = (root / "deps.edn").read_text()
            self.assertIn('"2606010002"', src)
            self.assertEqual(vdep.find_unregistered_adrs(root / "deps.edn", root), [])
            # still parseable + canonical
            self.assertEqual(vdep.fde.format_once(src), src)

    def test_unregistered_gates_exit_1_without_baseline(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make(
                tmp,
                '{:adrs [{:id "2606010001" :path "90-docs/adr/2606010001-a.md"} {:id "2606010009" :path "90-docs/adr/2606010009-z.md"}]}',
                [("2606010001-a.md", "A"), ("2606010002-b.md", "B"), ("2606010009-z.md", "Z")],
            )
            rc = vdep.main(["--repo-root", str(root), "--deps-edn", str(root / "deps.edn"), "--no-baseline"])
            self.assertEqual(rc, 1)
            # baseline v2 freeze → passes
            (root / "70-tools/scripts/lint").mkdir(parents=True)
            vdep.main(["--repo-root", str(root), "--deps-edn", str(root / "deps.edn"), "--write-baseline"])
            rc = vdep.main(["--repo-root", str(root), "--deps-edn", str(root / "deps.edn")])
            self.assertEqual(rc, 0)

    def test_v1_list_baseline_still_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make(
                tmp,
                '{:adrs [{:id "2606010001" :path "90-docs/adr/gone.md"} {:id "2606010009" :path "90-docs/adr/2606010009-z.md"}]}',
                [("2606010009-z.md", "Z")],
            )
            bl = root / "70-tools/scripts/lint"
            bl.mkdir(parents=True)
            import json as js
            (bl / "deps-edn-paths-baseline.json").write_text(js.dumps(["90-docs/adr/gone.md"]))
            rc = vdep.main(["--repo-root", str(root), "--deps-edn", str(root / "deps.edn")])
            self.assertEqual(rc, 0)


class BaselineRatchetTest(unittest.TestCase):
    def run_main(self, root, args):
        return vdep.main(["--repo-root", str(root), "--deps-edn", str(root / "deps.edn"), *args])

    def test_baseline_freezes_then_blocks_only_new_drift(self):
        with tempfile.TemporaryDirectory() as d:
            root = make_repo(
                pathlib.Path(d),
                '{:adrs [{:id "1" :path "legacy-gone.md"} {:id "2" :path "x.md"}]}',
                files=["x.md"],
            )
            (root / "70-tools/scripts/lint").mkdir(parents=True)
            # without baseline: drift → exit 1
            self.assertEqual(self.run_main(root, ["--no-baseline"]), 1)
            # freeze, then audit passes
            self.assertEqual(self.run_main(root, ["--write-baseline"]), 0)
            self.assertEqual(self.run_main(root, []), 0)
            # NEW drift on top of baseline → exit 1 again
            (root / "deps.edn").write_text(
                '{:adrs [{:id "1" :path "legacy-gone.md"} {:id "2" :path "x.md"}'
                ' {:id "3" :path "new-gone.md"}]}'
            )
            self.assertEqual(self.run_main(root, []), 1)

    def test_parse_error_exits_2(self):
        with tempfile.TemporaryDirectory() as d:
            root = make_repo(pathlib.Path(d), '{:adrs [{:id "1" :path "broken ]}')
            self.assertEqual(self.run_main(root, []), 2)


if __name__ == "__main__":
    unittest.main()
