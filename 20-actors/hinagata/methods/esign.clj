;; ported from /Users/junkawasaki/github/com-junkawasaki/orgs/etzhayyim/root/20-actors/hinagata/methods/esign.py (unit_refactor stage 0)
;; hinagata 雛形 — electronic-contract bridge: template → esign envelope → signature verify.
(ns root.hinagata.methods.esign
  (:require [clojure.string :as str]
            [clojure.set :as set]
            [clojure.edn :as edn]))

(declare has-clause render-document build-envelope verify-signature check-completion main)

(def HAS_CLAUSE ":has-clause")
(def CITE_KINDS (set [":cites-statute" ":mandated-by"]))

;; TODO: port-failed unit render_document (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmpebb8dc8v/scratch.clj:54:32: )
;; def render_document(template_id: str, nodes: dict, edges: list, fields: dict | None = None) -> str:
;;     """Deterministically render a template into a contract body (the bytes that get signed).
;; 
;;     The body lists, in stable order, the template's clauses and the public statute each clause
;;     rests on — so the signed document itself carries its statutory provenance (every clause
;;     traceable to the actual law it cites). `fields` fills party/term placeholders; missing
;;     fields render as explicit `[___]` blanks (never invented). PUBLIC reference only (G1).
;;     """
;;     fields = fields or {}
;;     t = nodes.get(template_id)
;;     if not t or t.get(":lt/kind") != ":template":
;;         raise ValueError(f"not a template: {template_id}")
;; 
;;     # clauses attached to this template, in graph order (deterministic)
;;     clause_ids = [e[":en/to"] for e in edges
;;                   if e.get(":en/kind") == HAS_CLAUSE and e.get(":en/from") == template_id]
;;     cites = {}
;;     for e in edges:
;;         if e.get(":en/kind") in CITE_KINDS:
;;             cites.setdefault(e[":en/from"], []).append(e[":en/to"])
;; 
;;     L = []
;;     L.append(f"# {t.get(':template/title', template_id)}")
;;     L.append("")
;;     L.append(f"Language: {t.get(':template/lang', '—')}  ·  "
;;              f"License: {t.get(':template/license', 'Apache-2.0')} + etzhayyim Charter Rider  ·  "
;;              f"Version: {t.get(':template/version', '—')}  ·  "
;;              f"Disclosed stance: {str(t.get(':template/stance', '—')).lstrip(':')}")
;;     L.append("")
;;     L.append("> This is a FAIR, openly-licensed template from the hinagata 雛形 commons. It is "
;;              "NOT legal advice and NOT a substitute for counsel. The parties execute it as "
;;              "their own act. Each clause cites the public law it rests on, for traceability.")
;;     L.append("")
;;     # party / term fields (filled or explicit blanks — never invented)
;;     L.append("## Parties & Terms")
;;     for key in ("party_a", "party_b", "effective_date", "term", "governing_law", "amount"):
;;         if key in fields:
;;             L.append(f"- {key}: {fields[key]}")
;;         else:
;;             L.append(f"- {key}: [___]")
;;     L.append("")
;;     L.append("## Clauses")
;;     for i, cid in enumerate(clause_ids, 1):
;;         c = nodes.get(cid, {})
;;         role = str(c.get(":clause/role", "—")).lstrip(":")
;;         opt = str(c.get(":clause/optionality", "—")).lstrip(":")
;;         L.append(f"### {i}. {c.get(':lt/label', cid)}  ({role}, {opt})")
;;         st = cites.get(cid, [])
;;         if st:
;;             refs = "; ".join(
;;                 f"{nodes.get(s, {}).get(':statute/citation', s)} "
;;                 f"({nodes.get(s, {}).get(':statute/instrument', '')})".strip()
;;                 for s in st)
;;             L.append(f"_Rests on:_ {refs}")
;;         L.append("")
;;     L.append("## Execution")
;;     L.append("Executed electronically via the etzhayyim esign substrate "
;;              "(com.etzhayyim.esign.envelope): each party signs with a WebAuthn passkey bound to "
;;              "their DID. Electronic execution rests on eIDAS Art. 25 (EU), ESIGN/UETA (US) and "
;;              "電子署名法 (JP), as cited by the signature clause.")
;;     L.append("")
;;     return "\n".join(L) + "\n"
(defn render-document [& _]
  (throw (ex-info "TODO: port-failed" {:from "render_document"})))

;; TODO: port-failed unit build_envelope (assembled-lint error)
;; def build_envelope(document: str, requester_did: str, signer_dids: list[str],
;;                    subject: str = "", signing_order: str = "parallel",
;;                    created_at: str = "1970-01-01T00:00:00Z") -> dict:
;;     """Construct the UNSIGNED com.etzhayyim.esign.envelope record for a rendered document.
;; 
;;     The document body is content-addressed (kotoba IPFS CIDv1 raw) and SHA-256 hashed — the
;;     two independent integrity anchors the lexicon requires. hinagata produces this record; it
;;     is then written to the requester's repo and signed client-side (no server key)."""
;;     body = document.encode("utf-8")
;;     if not signer_dids:
;;         raise ValueError("at least one signer required")
;;     if signing_order not in ("sequential", "parallel"):
;;         raise ValueError(f"signing_order must be sequential|parallel, got {signing_order}")
;;     return {
;;         "$type": "com.etzhayyim.esign.envelope",
;;         "requesterDid": requester_did,
;;         "subject": subject[:256],
;;         "documentCid": cidv1_raw(body),
;;         "documentSha256": sha256_hex(body),
;;         "documentMimeType": "text/markdown",
;;         "signers": list(signer_dids),
;;         "signingOrder": signing_order,
;;         "status": "pending",
;;         "createdAt": created_at,
;;     }
(defn build-envelope [& _]
  (throw (ex-info "TODO: port-failed" {:from "build_envelope"})))

(defn verify-signature [envelope signature]
  "Structurally verify a com.etzhayyim.esign.signature against its envelope.

  Checks the bindings hinagata CAN check without a key: signer is on the roster, the document
  hash the signer attested matches the envelope (anti-tamper), and the WebAuthn algorithm is
  an accepted one. The CRYPTOGRAPHIC assertion verification (WebAuthn / DID-key) is done by
  kotoba-auth, not here — this is the structural gate that precedes it."
  (let [reasons []
        signer-did (get signature "signerDid")
        signers (get envelope "signers" [])
        doc-sha256 (get signature "documentSha256")
        env-sha256 (get envelope "documentSha256")
        webauthn-alg (get signature "webauthnAlgorithm")
        assertion-envelope (get signature "assertionEnvelope")]
    (if (not (contains? signers signer-did))
      (conj reasons "signerDid not in envelope.signers roster")
      reasons)
    (if (not= doc-sha256 env-sha256)
      (conj reasons "documentSha256 mismatch (document tampered between request and sign)")
      reasons)
    (if (not (contains? #{"ES256" "EdDSA"} webauthn-alg))
      (conj reasons (str "unsupported webauthn algorithm: " webauthn-alg))
      reasons)
    (if (nil assertion-envelope)
      (conj reasons "missing assertionEnvelope (encrypted WebAuthn assertion)")
      reasons)
    (let [final-reasons (apply list reasons)]
      [(count final-reasons) == 0 final-reasons])))

;; TODO: port-failed unit check_completion (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmp3hf47tzx/scratch.clj:6:44: w)
;; def check_completion(envelope: dict, signatures: list[dict],
;;                      completed_at: str = "1970-01-01T00:00:00Z") -> dict | None:
;;     """Return a com.etzhayyim.esign.completedEvent iff every roster signer has a VALID signature.
;; 
;;     For `sequential` order, signatures must also arrive in the roster order."""
;;     signers = envelope.get("signers", [])
;;     valid_by_did = {}
;;     for sig in signatures:
;;         ok, _ = verify_signature(envelope, sig)
;;         if ok:
;;             valid_by_did[sig["signerDid"]] = sig
;;     if not all(did in valid_by_did for did in signers):
;;         return None
;;     ordered = [valid_by_did[did] for did in signers]  # roster order
;;     if envelope.get("signingOrder") == "sequential":
;;         # all present (checked above); sequential ordering is enforced by the roster order we build
;;         pass
;;     return {
;;         "$type": "com.etzhayyim.esign.completedEvent",
;;         "envelopeCid": envelope.get("documentCid"),
;;         "documentCid": envelope.get("documentCid"),
;;         "documentSha256": envelope.get("documentSha256"),
;;         "signatureCount": len(ordered),
;;         "completedAt": completed_at,
;;     }
(defn check-completion [& _]
  (throw (ex-info "TODO: port-failed" {:from "check_completion"})))

;; TODO: port-failed unit main (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmpkbly8pkt/scratch.clj:3:15: w)
;; def main(argv):
;;     here = pathlib.Path(__file__).resolve().parent.parent
;;     seed = here / "data" / "seed-legal-template-graph.kotoba.edn"
;;     if len(argv) > 1 and not argv[1].startswith("--"):
;;         seed = pathlib.Path(argv[1])
;;     template_id = argv[argv.index("--template") + 1] if "--template" in argv else "tmpl.nda-mutual"
;;     requester = argv[argv.index("--requester") + 1] if "--requester" in argv \
;;         else "did:web:etzhayyim.com:actor:hinagata"
;;     signers = [argv[i + 1] for i, a in enumerate(argv) if a == "--signer"]
;;     if not signers:
;;         signers = ["did:plc:alice", "did:plc:bob"]
;;     outdir = pathlib.Path(argv[argv.index("--out") + 1]) if "--out" in argv else here / "out"
;;     outdir.mkdir(parents=True, exist_ok=True)
;; 
;;     nodes, edges = load(seed)
;;     doc = render_document(template_id, nodes, edges)
;;     env = build_envelope(doc, requester, signers, subject=nodes[template_id].get(":template/title", ""))
;; 
;;     (outdir / f"contract-{template_id}.md").write_text(doc, encoding="utf-8")
;;     (outdir / f"envelope-{template_id}.json").write_text(
;;         json.dumps(env, ensure_ascii=False, indent=2), encoding="utf-8")
;;     print(f"hinagata esign: {template_id} → {len(doc.encode())} B")
;;     print(f"  documentCid:    {env['documentCid']}")
;;     print(f"  documentSha256: {env['documentSha256']}")
;;     print(f"  signers:        {', '.join(signers)} ({env['signingOrder']})")
;;     print(f"  → {outdir/('envelope-'+template_id+'.json')} (UNSIGNED; member signs client-side)")
;;     return 0
(defn main [& _]
  (throw (ex-info "TODO: port-failed" {:from "main"})))

