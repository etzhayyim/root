;; ported from 70-tools/e7m-sim/scenes/giemon_kabitori/sbom_gen.py (unit_refactor stage 0)
;; giemon kabitori — generate CycloneDX SBOM + kotoba ingest body from parts.edn.
(ns e7m-sim.scenes.giemon-kabitori.sbom-gen
  (:require [clojure.string] [clojure.set] [clojure.edn]))

(declare edn-reader parse-edn claim-keys claim-pred to-kotoba-entities to-cyclonedx main)

;; TODO: port-failed unit _EdnReader (/var/folders/px/b63lssbx5056kq_1t6pvc1f80000gn/T/tmptnz_f7k_/scratch.clj:13:20: )
;; class _EdnReader:
;;     def __init__(self, text):
;;         self.s = text
;;         self.i = 0
;;         self.n = len(text)
;; 
;;     def _err(self, msg):
;;         raise ValueError(f"edn parse error at {self.i}: {msg}")
;; 
;;     def _skip_ws(self):
;;         while self.i < self.n:
;;             c = self.s[self.i]
;;             if c == ';':  # line comment
;;                 while self.i < self.n and self.s[self.i] != '\n':
;;                     self.i += 1
;;             elif c in ' \t\r\n,':
;;                 self.i += 1
;;             else:
;;                 break
;; 
;;     def read(self):
;;         self._skip_ws()
;;         if self.i >= self.n:
;;             self._err("unexpected EOF")
;;         c = self.s[self.i]
;;         if c == '{':
;;             return self._read_map()
;;         if c == '[':
;;             return self._read_vec()
;;         if c == '"':
;;             return self._read_str()
;;         if c == ':':
;;             return self._read_kw()
;;         return self._read_atom()
;; 
;;     def _read_map(self):
;;         self.i += 1  # {
;;         d = {}
;;         while True:
;;             self._skip_ws()
;;             if self.i >= self.n:
;;                 self._err("unterminated map")
;;             if self.s[self.i] == '}':
;;                 self.i += 1
;;                 return d
;;             k = self.read()
;;             v = self.read()
;;             d[k] = v
;; 
;;     def _read_vec(self):
;;         self.i += 1  # [
;;         out = []
;;         while True:
;;             self._skip_ws()
;;             if self.i >= self.n:
;;                 self._err("unterminated vector")
;;             if self.s[self.i] == ']':
;;                 self.i += 1
;;                 return out
;;             out.append(self.read())
;; 
;;     def _read_str(self):
;;         self.i += 1  # opening quote
;;         buf = []
;;         while self.i < self.n:
;;             c = self.s[self.i]
;;             if c == '\\':
;;                 self.i += 1
;;                 esc = self.s[self.i]
;;                 buf.append({'n': '\n', 't': '\t', 'r': '\r'}.get(esc, esc))
;;             elif c == '"':
;;                 self.i += 1
;;                 return ''.join(buf)
;;             else:
;;                 buf.append(c)
;;             self.i += 1
;;         self._err("unterminated string")
;; 
;;     def _read_kw(self):
;;         self.i += 1  # leading colon
;;         start = self.i
;;         while self.i < self.n and (self.s[self.i].isalnum() or self.s[self.i] in '/-.*_'):
;;             self.i += 1
;;         return self.s[start:self.i]  # keyword name without the colon
;; 
;;     def _read_atom(self):
;;         start = self.i
;;         while self.i < self.n and (self.s[self.i].isalnum() or self.s[self.i] in '-.+'):
;;             self.i += 1
;;         tok = self.s[start:self.i]
;;         if tok == 'true':
;;             return True
;;         if tok == 'false':
;;             return False
;;         if tok == 'nil':
;;             return None
;;         try:
;;             return int(tok)
;;         except ValueError:
;;             return tok
(defn edn-reader [& _]
  (throw (ex-info "TODO: port-failed" {:from "_EdnReader"})))

;; TODO: port-failed unit parse_edn (/var/folders/px/b63lssbx5056kq_1t6pvc1f80000gn/T/tmphp9vqf9n/scratch.clj:2:1: er)
;; def parse_edn(text):
;;     return _EdnReader(text).read()
(defn parse-edn [& _]
  (throw (ex-info "TODO: port-failed" {:from "parse_edn"})))

(def _claim-keys [
  "part/group"
  "part/procurement"
  "part/manufacturer"
  "part/product"
  "part/mpn"
  "part/purl"
  "part/qty"
  "part/mass-g"
  "part/unit-jpy"
  "part/supplier"
  "part/sim-feature"
  "part/fab-process"
  "part/sourcing"
  "part/note"])

;; TODO: port-failed unit _claim_pred (/var/folders/px/b63lssbx5056kq_1t6pvc1f80000gn/T/tmpqamzipnc/scratch.clj:3:8: er)
;; def _claim_pred(k):
;;     # part/mass-g -> part/massG ; part/sim-feature -> part/simFeature ; part/fab-process -> part/fabProcess
;;     head, tail = k.split('/', 1)
;;     parts = tail.split('-')
;;     camel = parts[0] + ''.join(w.capitalize() for w in parts[1:])
;;     return f"{head}/{camel}"
(defn claim-pred [& _]
  (throw (ex-info "TODO: port-failed" {:from "_claim_pred"})))

;; TODO: port-failed unit to_kotoba_entities (/var/folders/px/b63lssbx5056kq_1t6pvc1f80000gn/T/tmph01odkzj/scratch.clj:20:1: e)
;; def to_kotoba_entities(meta, parts):
;;     bom_of = meta.get("bom/of", "giemon-kabitori")
;;     entities = []
;;     for p in parts:
;;         claims = [{"pred": "part/bom", "value": bom_of}]
;;         for k in _CLAIM_KEYS:
;;             if k in p and p[k] is not None:
;;                 claims.append({"pred": _claim_pred(k), "value": str(p[k])})
;;         entities.append({
;;             "id": p["part/id"],
;;             "type": "GiemonKabitoriPart",
;;             "labelEn": p.get("part/name", p["part/id"]),
;;             "claims": claims,
;;         })
;;     return {"entities": entities}
(defn to-kotoba-entities [& _]
  (throw (ex-info "TODO: port-failed" {:from "to_kotoba_entities"})))

;; TODO: port-failed unit to_cyclonedx (/var/folders/px/b63lssbx5056kq_1t6pvc1f80000gn/T/tmprxvirs6a/scratch.clj:2:1: er)
;; def to_cyclonedx(meta, parts):
;;     components = []
;;     for p in parts:
;;         props = [{"name": f"giemon:{_claim_pred(k).replace('part/', '')}", "value": str(p[k])}
;;                  for k in _CLAIM_KEYS if k in p and p[k] is not None]
;;         comp = {
;;             "type": "device",
;;             "bom-ref": p["part/id"],
;;             "name": p.get("part/name", p["part/id"]),
;;             "properties": props,
;;         }
;;         if p.get("part/manufacturer"):
;;             comp["publisher"] = p["part/manufacturer"]
;;             comp["supplier"] = {"name": p["part/manufacturer"]}
;;         if p.get("part/product"):
;;             comp["version"] = str(p["part/product"])
;;         if p.get("part/purl"):
;;             comp["purl"] = p["part/purl"]
;;         components.append(comp)
;;     return {
;;         "bomFormat": "CycloneDX",
;;         "specVersion": "1.5",
;;         "version": 1,
;;         "metadata": {
;;             "component": {
;;                 "type": "device",
;;                 "name": meta.get("bom/title", "Giemon Kabitori probe"),
;;                 "version": meta.get("bom/revision", "v1"),
;;             },
;;             "properties": [
;;                 {"name": "giemon:bomOf", "value": meta.get("bom/of", "giemon-kabitori")},
;;                 {"name": "giemon:sourcing", "value": meta.get("bom/sourcing", "representative")},
;;                 {"name": "giemon:note", "value": meta.get("bom/note", "")},
;;             ],
;;         },
;;         "components": components,
;;     }
(defn to-cyclonedx [& _]
  (throw (ex-info "TODO: port-failed" {:from "to_cyclonedx"})))

;; TODO: port-failed unit main (/var/folders/px/b63lssbx5056kq_1t6pvc1f80000gn/T/tmp5e_gm3ju/scratch.clj:3:15: e)
;; def main():
;;     here = Path(__file__).resolve().parent
;;     edn_path = Path(sys.argv[1]) if len(sys.argv) > 1 else here / "parts.edn"
;;     out_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else here
;;     doc = parse_edn(edn_path.read_text(encoding="utf-8"))
;; 
;;     meta = doc["bom/meta"]
;;     parts = doc["bom/parts"]
;; 
;;     # self-check
;;     assert isinstance(parts, list) and len(parts) > 0, "no parts parsed"
;;     for p in parts:
;;         for req in ("part/id", "part/name", "part/group", "part/procurement"):
;;             assert req in p, f"{p.get('part/id','?')} missing {req}"
;;     n_cots = sum(1 for p in parts if p["part/procurement"] == "cots")
;;     n_fab = sum(1 for p in parts if p["part/procurement"] == "custom-fab")
;; 
;;     cdx = to_cyclonedx(meta, parts)
;;     ing = to_kotoba_entities(meta, parts)
;;     # Output names derive from :bom/of (e.g. giemon-kabitori → kabitori) so
;;     # multiple robots' artifacts coexist in one directory.
;;     slug = str(meta.get("bom/of", "robot")).removeprefix("giemon-")
;;     cdx_path = out_dir / f"{slug}.cdx.json"
;;     ing_path = out_dir / f"{slug}.ingest.json"
;;     cdx_path.write_text(json.dumps(cdx, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
;;     ing_path.write_text(json.dumps(ing, ensure_ascii=False) + "\n", encoding="utf-8")
;; 
;;     print(f"{slug}: parts={len(parts)}  cots={n_cots}  custom-fab={n_fab}")
;;     print(f"wrote {cdx_path} ({len(cdx['components'])} components)")
;;     print(f"wrote {ing_path} ({len(ing['entities'])} entities)")
(defn main [& _]
  (throw (ex-info "TODO: port-failed" {:from "main"})))

