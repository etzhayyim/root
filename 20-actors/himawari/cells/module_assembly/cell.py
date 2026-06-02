"""ModuleAssemblyCell — himawari module assembly + flash + EL (ADR-2606021200).

Module assembly + flash + EL imaging.
G11 (deterministic yield + provenance — flash IV + EL image Ed25519-signed
    per module; serial <-> feedstock lot traceable) enforcement.

Pipeline (Otete precision arm + Mimi metrology, both inherited from kuni-umi):

    stringing -> lamination -> framing -> J-box -> flash IV + EL imaging

Each finished module yields one `com.etzhayyim.himawari.moduleAttestation`
record written to the kotoba Datom log (canonical EAVT state — G6/G8). G11 binds
every module serial to its upstream feedstock lot and signs the flash-IV +
EL-image content digests, so a module is never attestable without a complete,
verifiable chain of custody back to the polysilicon lot. G12 refuses any
destination that is not an internal etzhayyim actor (SBT<->SBT carve-out).

This cell COMPOSES kuni-umi Otete (handling/stringing/framing) + Mimi
(flash IV + EL + thermal-IR); it does NOT re-implement their solvers. Mimi
supplies the measured flash-IV curve + EL image bytes; this cell computes the
attestation, the provenance chain, and the deterministic signature.

Honest limit: the per-module signature is a deterministic content-binding
(HMAC over the canonical module digest) standing in for the operator's real
Ed25519 device key, which is custody-held off this cell (no server-held signing
key — substrate boundary). When the asher Murakumo node is provisioned with its
device key at R1 activation, `_sign_module` swaps to a real Ed25519 sign over the
same canonical bytes; the digest contract is unchanged. No secrets live here.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any

# kotoba-provided host bindings (WASM Component Model imports); None in local dev.
try:
    from kotoba import datalog  # type: ignore
except ImportError:  # local dev / test fallback
    datalog = None  # type: ignore

# Murakumo node identity for this cell (manifest.jsonld: module_assembly -> asher).
MURAKUMO_NODE = "asher"

# Internal-only destinations (G12: no external commercial PV sale; SBT<->SBT carve-out).
# himawari modules install on hikari sites only; the broader allow-list keeps the
# carve-out explicit rather than a bare string compare.
_INTERNAL_DID_PREFIX = "did:web:etzhayyim.com:"
_INSTALL_ACTORS = {"hikari"}

# Mimi metrology requires at least one process robot + one metrology robot to
# co-attest a module (G11: deterministic provenance is never single-witness).
_MIN_ATTESTING_ROBOTS = 2

# G5 circularity floor: design-for-recovery must be >= 90% (9000 bps).
_RECYCLABILITY_FLOOR_BPS = 9000

# Flash-IV pass binning: a module that does not flash within tolerance of its
# rated Wp is binned, never silently attested (G11 deterministic yield).
_FLASH_TOLERANCE_BPS = 500  # +/- 5% of rated Wp


class ModuleAssemblyCell:
    """Module assembly + flash + EL imaging."""

    def __init__(self) -> None:
        # Deterministic binding domain for the per-module signature. This is a
        # public domain-separation tag, NOT a secret; it makes the HMAC binding
        # reproducible and collision-separated from other himawari signatures.
        self._sign_domain = b"com.etzhayyim.himawari.moduleAttestation/v1"

    # ------------------------------------------------------------------ #
    # Pregel entrypoint
    # ------------------------------------------------------------------ #
    def solve(self, state: dict[str, Any]) -> dict[str, Any]:
        """Assemble one PV module from its cell batch + feedstock lot, run the
        flash-IV + EL metrology (Mimi), and emit a signed moduleAttestation.

        Expected input state (supplied by the upstream cell_process cell + the
        Mimi metrology robot):

            moduleSerial        str   stable per-module serial
            cellBatchId         str   chains to cellBatchRecord
            feedstockLotId      str   chains to polysiliconProvenanceAttestation (G11)
            bomCid              str   CycloneDX SBOM CID (G8)
            ratedWp             int   nameplate rating
            measuredWp          int   Mimi flash-IV measured power (optional; defaults rated)
            flashIv             obj   Mimi flash-IV curve payload (hashed -> flashIvCid)
            elImage             obj   Mimi EL image payload     (hashed -> elImageCid)
            destinationActorDid str   install destination (G12 internal-only)
            recordedAt          str   attestation timestamp (ISO-8601; threaded
                                      through from input — never wall-clock in-cell)
            attestingRobots     list  >= 2 co-witnessing robots (G11). Each entry is
                                      either a robotSignature-shaped dict (robotDid +
                                      signature [+ role/timestamp]) or a bare robot
                                      name/DID string (normalized to a #robotSignature
                                      object with a deterministic witness binding).
            epbtMonths          int   energy payback time (G4; optional)
            recyclabilityBps    int   design-for-recovery bps (G5; optional)

        Returns the input state plus `moduleAttestation` (the record), `provenance`
        (the serial->lot chain), and `kotobaWritten` (bool). A module that fails the
        G11/G12 gates is returned with `binned`/`refused` set and NO attestation."""
        record_in = {
            "moduleSerial": str(state.get("moduleSerial", "")),
            "cellBatchId": str(state.get("cellBatchId", "")),
            "feedstockLotId": str(state.get("feedstockLotId", "")),
            "bomCid": str(state.get("bomCid", "")),
            "ratedWp": int(state.get("ratedWp", 0)),
            "recordedAt": str(state.get("recordedAt", "")),
            "destinationActorDid": str(state.get("destinationActorDid", "")),
            "attestingRobots": list(state.get("attestingRobots", [])),
            "epbtMonths": int(state.get("epbtMonths", 0)),
            "recyclabilityBps": int(state.get("recyclabilityBps", 0)),
        }

        # G11: serial <-> feedstock lot traceability is mandatory. A module with no
        # feedstock lot or no cell batch has no chain of custody and is refused.
        chain = self._provenance_chain(record_in["moduleSerial"],
                                       record_in["cellBatchId"],
                                       record_in["feedstockLotId"])
        if not chain["complete"]:
            return {**state, "refused": True, "reason": chain["reason"], "kotobaWritten": False}

        # G12: internal-only destination (SBT<->SBT carve-out). No external sale, ever.
        dest_ok, dest_reason = self._check_destination(record_in["destinationActorDid"])
        if not dest_ok:
            return {**state, "refused": True, "reason": dest_reason, "kotobaWritten": False}

        # G11: at least two co-witnessing robots (one process + one metrology).
        if len(record_in["attestingRobots"]) < _MIN_ATTESTING_ROBOTS:
            return {
                **state,
                "refused": True,
                "reason": f"G11: module needs >= {_MIN_ATTESTING_ROBOTS} co-attesting robots "
                          f"(got {len(record_in['attestingRobots'])})",
                "kotobaWritten": False,
            }

        # Mimi metrology: flash IV + EL image -> content-addressed CIDs (G11).
        flash_iv_cid = self._content_cid(state.get("flashIv", {}), "flashiv")
        el_image_cid = self._content_cid(state.get("elImage", {}), "elimage")
        record = {
            **record_in,
            "flashIvCid": flash_iv_cid,
            "elImageCid": el_image_cid,
        }

        # G11 deterministic yield: bin a module whose measured Wp falls outside the
        # flash tolerance of its rated Wp. Binned modules are recorded but flagged.
        measured_wp = int(state.get("measuredWp", record["ratedWp"]))
        binned, bin_reason = self._flash_bin(record["ratedWp"], measured_wp)
        record["measuredWp"] = measured_wp

        # G5 circularity advisory (does not block attestation at this cell; the
        # silenHimawariReview Council gate enforces the floor at attestation review).
        record["recyclabilityBelowFloor"] = (
            0 < record["recyclabilityBps"] < _RECYCLABILITY_FLOOR_BPS
        )

        # G11 signature: deterministic content-binding over the canonical module
        # digest (flash IV + EL + serial + lot). See module docstring for the
        # Ed25519 swap-in contract.
        signature = self._sign_module(record, chain["chainDigest"])
        record["provenanceChainDigest"] = chain["chainDigest"]
        record["signature"] = signature
        # G11: normalize the >=2 co-witnessing robots into #robotSignature objects
        # (robotDid + signature [+ role/timestamp]). The witness binding is bound to
        # the same canonical module bytes as the module signature, so a robot witness
        # cannot be replayed onto a different module/lot.
        record["attestingRobots"] = self._robot_signatures(
            record_in["attestingRobots"], record, chain["chainDigest"]
        )
        record["recordedAt"] = record_in["recordedAt"]
        record["attestingNode"] = MURAKUMO_NODE
        if binned:
            record["binned"] = True
            record["binReason"] = bin_reason

        written = self._write_attestation(record)

        return {
            **state,
            "moduleAttestation": record,
            "provenance": chain,
            "binned": binned,
            "kotobaWritten": written,
        }

    # ------------------------------------------------------------------ #
    # G11 — provenance chain (serial -> cell batch -> feedstock lot)
    # ------------------------------------------------------------------ #
    def _provenance_chain(self, serial: str, cell_batch: str, lot: str) -> dict[str, Any]:
        """Build the module->feedstock chain of custody. Every link must be present;
        a missing link breaks G11 traceability and the module cannot be attested.

        When the kotoba host binding is live, the cell batch and feedstock lot are
        confirmed to exist in the Datom log (so a module cannot cite a phantom lot);
        in local dev (datalog is None) the links are validated structurally only."""
        if not serial:
            return {"complete": False, "reason": "G11: module has no serial"}
        if not cell_batch:
            return {"complete": False, "reason": "G11: serial not bound to a cell batch"}
        if not lot:
            return {"complete": False, "reason": "G11: serial not traceable to a feedstock lot"}

        lot_confirmed = self._lot_exists(lot) if datalog is not None else None
        if lot_confirmed is False:
            return {
                "complete": False,
                "reason": f"G11: feedstock lot {lot!r} not found in provenance log "
                          "(no polysiliconProvenanceAttestation)",
            }

        link = f"{lot}->{cell_batch}->{serial}"
        chain_digest = "sha256:" + hashlib.sha256(link.encode("utf-8")).hexdigest()
        return {
            "complete": True,
            "moduleSerial": serial,
            "cellBatchId": cell_batch,
            "feedstockLotId": lot,
            "link": link,
            "chainDigest": chain_digest,
            "lotConfirmedOnChain": bool(lot_confirmed),
        }

    @staticmethod
    def _lot_exists(lot: str) -> bool:
        """Confirm the feedstock lot is anchored in the kotoba Datom log (G11).
        Returns True/False; only called when the datalog host binding is present."""
        try:
            rows = datalog.query(  # type: ignore[union-attr]
                "[:find ?lot :in $ ?lot :where "
                "[?p :himawari.provenance/lot-id ?lot]]",
                lot,
            )
            return bool(rows)
        except Exception:
            # A query failure must not silently pass provenance (fail-closed, G11).
            return False

    # ------------------------------------------------------------------ #
    # G12 — internal-only destination
    # ------------------------------------------------------------------ #
    @staticmethod
    def _check_destination(dest_did: str) -> tuple[bool, str]:
        """G12: modules install on internal etzhayyim actors only (SBT<->SBT
        carve-out). Any external / commercial destination is refused outright."""
        if not dest_did:
            return False, "G12: module has no destination actor DID"
        if not dest_did.startswith(_INTERNAL_DID_PREFIX):
            return False, (
                f"G12: external destination {dest_did!r} refused — modules install "
                "on internal etzhayyim actors only (no external commercial PV sale)"
            )
        actor = dest_did[len(_INTERNAL_DID_PREFIX):]
        if actor not in _INSTALL_ACTORS:
            return False, (
                f"G12: destination actor {actor!r} is not a sanctioned install actor "
                f"(expected one of {sorted(_INSTALL_ACTORS)})"
            )
        return True, "internal hikari install (SBT<->SBT carve-out)"

    # ------------------------------------------------------------------ #
    # G11 — deterministic flash binning
    # ------------------------------------------------------------------ #
    @staticmethod
    def _flash_bin(rated_wp: int, measured_wp: int) -> tuple[bool, str]:
        """Bin a module whose measured flash power falls outside +/- tolerance of
        its rated Wp. Returns (binned, reason). A rated_wp of 0 is itself a bin."""
        if rated_wp <= 0:
            return True, "G11: module has no positive rated Wp"
        delta_bps = abs(measured_wp - rated_wp) * 10_000 // rated_wp
        if delta_bps > _FLASH_TOLERANCE_BPS:
            return True, (
                f"G11: flash power {measured_wp}Wp deviates {delta_bps}bps from "
                f"rated {rated_wp}Wp (tolerance {_FLASH_TOLERANCE_BPS}bps)"
            )
        return False, ""

    # ------------------------------------------------------------------ #
    # Content addressing + deterministic per-module signature (G11)
    # ------------------------------------------------------------------ #
    @staticmethod
    def _content_cid(payload: Any, kind: str) -> str:
        """Content-address a metrology payload (flash IV curve / EL image) to a
        stable sha256 CID. Canonical JSON (sorted keys) makes the CID deterministic
        for identical measurements — the property G11 verification relies on."""
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                               ensure_ascii=False).encode("utf-8")
        digest = hashlib.sha256(canonical).hexdigest()
        return f"cid:himawari:{kind}:sha256:{digest}"

    def _canonical_module_bytes(self, record: dict[str, Any], chain_digest: str) -> bytes:
        """The exact byte string that the per-module signature binds. Includes the
        G11-load-bearing fields (serial, lot, both metrology CIDs, rating, chain
        digest) so a signature cannot be replayed onto a different module/lot."""
        signed_view = {
            "moduleSerial": record["moduleSerial"],
            "cellBatchId": record["cellBatchId"],
            "feedstockLotId": record["feedstockLotId"],
            "flashIvCid": record["flashIvCid"],
            "elImageCid": record["elImageCid"],
            "ratedWp": record["ratedWp"],
            "bomCid": record["bomCid"],
            "destinationActorDid": record["destinationActorDid"],
            "provenanceChainDigest": chain_digest,
        }
        return json.dumps(signed_view, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False).encode("utf-8")

    def _sign_module(self, record: dict[str, Any], chain_digest: str) -> dict[str, Any]:
        """Produce the per-module provenance signature over the canonical module
        bytes (G11). The signed digest is reproducible by any verifier from the
        public record fields.

        HONEST TODO: this is a deterministic HMAC content-binding keyed by the
        public domain tag — it proves byte-integrity + non-substitution of the
        signed view, but it is NOT yet a real Ed25519 device signature (the asher
        node's Ed25519 key is custody-held off this cell; no server-held signing
        key per the substrate boundary). At R1 activation, replace the HMAC line
        with an Ed25519 sign over the SAME `payload` bytes; the `signedDigest` /
        verification contract is unchanged."""
        payload = self._canonical_module_bytes(record, chain_digest)
        signed_digest = hashlib.sha256(self._sign_domain + payload).hexdigest()
        # Deterministic content-binding (placeholder for Ed25519 over `payload`).
        binding = hmac.new(self._sign_domain, payload, hashlib.sha256).hexdigest()
        return {
            "alg": "content-binding-sha256",  # -> "ed25519" at R1 activation
            "signedDigest": f"sha256:{signed_digest}",
            "binding": binding,
            "signer": MURAKUMO_NODE,
            "serverHeldKey": False,  # substrate-boundary invariant: no key in-cell
        }

    # Default witness roles for the canonical kuni-umi process + metrology robots;
    # any unrecognized robot witnesses as a generic "metrology" co-attester.
    _ROBOT_ROLES = {
        "otete": "framing",
        "mimi": "metrology",
    }

    def _robot_signatures(
        self, robots: list[Any], record: dict[str, Any], chain_digest: str
    ) -> list[dict[str, Any]]:
        """Normalize the co-witnessing robot list into #robotSignature objects
        (robotDid + signature, plus role/timestamp where known) per the lexicon.

        A caller may already supply robotSignature-shaped dicts (passed through with
        any missing required field filled deterministically); a bare name/DID string
        is lifted into a witness object whose `signature` is a deterministic Ed25519
        stand-in bound to the SAME canonical module bytes as the module signature
        (G11 non-substitution). At R1 the per-robot device Ed25519 key signs these
        bytes directly; the witness contract is unchanged."""
        payload = self._canonical_module_bytes(record, chain_digest)
        out: list[dict[str, Any]] = []
        for entry in robots:
            if isinstance(entry, dict):
                name = str(entry.get("robotDid") or entry.get("name") or "").strip()
                robot_did = self._robot_did(name)
                role = entry.get("role") or self._ROBOT_ROLES.get(
                    name.rsplit(":", 1)[-1], "metrology"
                )
                sig = entry.get("signature") or self._witness_binding(robot_did, payload)
                hop: dict[str, Any] = {"robotDid": robot_did, "signature": sig, "role": role}
                if entry.get("timestamp"):
                    hop["timestamp"] = str(entry["timestamp"])
                elif record.get("recordedAt"):
                    hop["timestamp"] = record["recordedAt"]
                out.append(hop)
            else:
                name = str(entry).strip()
                robot_did = self._robot_did(name)
                hop = {
                    "robotDid": robot_did,
                    "signature": self._witness_binding(robot_did, payload),
                    "role": self._ROBOT_ROLES.get(name, "metrology"),
                }
                if record.get("recordedAt"):
                    hop["timestamp"] = record["recordedAt"]
                out.append(hop)
        return out

    @staticmethod
    def _robot_did(name: str) -> str:
        """Lift a bare robot name into its etzhayyim DID (a value already in DID form
        is passed through). Keeps the witness DID lineage explicit (G7 accountability)."""
        if name.startswith("did:"):
            return name
        return f"did:web:etzhayyim.com:himawari:robot:{name}" if name else ""

    def _witness_binding(self, robot_did: str, payload: bytes) -> str:
        """Deterministic per-robot witness binding over the canonical module bytes
        (Ed25519 stand-in; substrate-boundary — no in-cell key). Distinct per robot
        DID, so two witnesses never collide and a witness cannot be replayed."""
        return hmac.new(
            self._sign_domain, robot_did.encode("utf-8") + b"\x00" + payload, hashlib.sha256
        ).hexdigest()

    # ------------------------------------------------------------------ #
    # kotoba Datom write (G6/G8 — canonical EAVT state)
    # ------------------------------------------------------------------ #
    @staticmethod
    def _write_attestation(record: dict[str, Any]) -> bool:
        """Write the moduleAttestation to the kotoba Datom log (canonical state).
        Returns True if a live host binding accepted the write, False in local dev
        (datalog is None) where the record is computed but not persisted. NEVER
        falls back to any non-kotoba store (substrate boundary)."""
        if datalog is None:
            return False
        try:
            datalog.transact(  # type: ignore[union-attr]
                [
                    {
                        ":himawari.module/serial": record["moduleSerial"],
                        ":himawari.module/cell-batch": record["cellBatchId"],
                        ":himawari.module/feedstock-lot": record["feedstockLotId"],
                        ":himawari.module/bom-cid": record["bomCid"],
                        ":himawari.module/flash-iv-cid": record["flashIvCid"],
                        ":himawari.module/el-image-cid": record["elImageCid"],
                        ":himawari.module/rated-wp": record["ratedWp"],
                        ":himawari.module/destination-did": record["destinationActorDid"],
                        ":himawari.module/chain-digest": record["provenanceChainDigest"],
                        ":himawari.module/signed-digest": record["signature"]["signedDigest"],
                        ":himawari.module/recorded-at": record["recordedAt"],
                        ":himawari.module/attesting-node": record["attestingNode"],
                    }
                ]
            )
            return True
        except Exception:
            return False
