#!/usr/bin/env python3
"""yotei — test harness (stdlib unittest; no kotoba host needed).

Verifies the structural invariants of ADR-2606072200:
  G4 no-double-book — overlapping slot refused at propose AND re-checked at confirm
  G5 no-server-key  — only a member signature confirms
  G8 consent-bound  — propose without consent refused
  G2 no-harvest     — booker contact only as an encrypted ref; no profile field
  slot generation   — booked slots absent, honest availability
"""
import unittest

import agent


CAL = "did:web:yotei.etzhayyim.com:calendar:alice"


def _confirmed(start, dur):
    return {"status": "confirmed", "calendarDid": CAL, "startEpochMin": start, "durationMin": dur}


def _req(start, dur=30, **kw):
    base = dict(bookingId="bk1", calendarDid=CAL, requesterDid="did:plc:bob",
                responderDid="did:plc:alice", startEpochMin=start, durationMin=dur,
                consentRef="consent-1")
    base.update(kw)
    return base


class Overlap(unittest.TestCase):
    def test_overlap_true(self):
        self.assertTrue(agent._overlaps(100, 30, 110, 30))

    def test_touching_not_overlap(self):
        self.assertFalse(agent._overlaps(100, 30, 130, 30))  # [100,130) and [130,160)

    def test_is_free_respects_only_confirmed(self):
        proposed = {"status": "proposed", "calendarDid": CAL, "startEpochMin": 100, "durationMin": 30}
        self.assertTrue(agent.is_free(CAL, 100, 30, [proposed]))   # proposed doesn't block
        self.assertFalse(agent.is_free(CAL, 100, 30, [_confirmed(100, 30)]))


class Propose(unittest.TestCase):
    def test_consent_required(self):
        out = agent.propose_booking(_req(600, consentRef=""), [])
        self.assertEqual(out["state"], "refused")
        self.assertIn("G8", out["reason"])

    def test_free_slot_proposed(self):
        out = agent.propose_booking(_req(600), [])
        self.assertEqual(out["state"], "proposed")
        self.assertIsNone(out["confirmedSig"])

    def test_double_book_refused(self):
        out = agent.propose_booking(_req(600), [_confirmed(600, 30)])
        self.assertEqual(out["state"], "refused")
        self.assertIn("G4", out["reason"])

    def test_contact_is_ref_only(self):
        out = agent.propose_booking(_req(600, contactRef="com.etzhayyim.encrypted:abcd"), [])
        # no plaintext profile/email/phone field exists
        for k in out:
            self.assertNotIn("email", k.lower())
            self.assertNotIn("phone", k.lower())
            self.assertNotIn("profile", k.lower())
        self.assertTrue(out["contactRef"].startswith("com.etzhayyim.encrypted:"))


class Confirm(unittest.TestCase):
    def setUp(self):
        self.proposed = agent.propose_booking(_req(600), [])

    def test_member_signature_confirms(self):
        out = agent.confirm_booking(self.proposed, {"origin": "member", "ref": "sig-1"}, [])
        self.assertEqual(out["status"], "confirmed")
        self.assertEqual(out["confirmedSig"], "sig-1")

    def test_server_signature_refused(self):
        out = agent.confirm_booking(self.proposed, {"origin": "server", "ref": "x"}, [])
        self.assertTrue(out["refused"])
        self.assertIn("G5", out["reason"])

    def test_race_lost_refused(self):
        # someone else's confirmed booking appears between propose and confirm
        out = agent.confirm_booking(self.proposed, {"origin": "member", "ref": "s"},
                                    [_confirmed(600, 30)])
        self.assertTrue(out["refused"])
        self.assertIn("G4", out["reason"])


class Slots(unittest.TestCase):
    def test_booked_slot_absent(self):
        avail = {"availabilityId": "a1", "calendarDid": CAL, "dayOfWeek": 0,
                 "startMin": 0, "endMin": 90, "slotMin": 30}
        # day midnight epoch = 0; window 0..90 → slots at 0,30,60. Book 30-60.
        slots = agent.generate_slots(avail, 0, [_confirmed(30, 30)])
        starts = [s["startEpochMin"] for s in slots]
        self.assertEqual(starts, [0, 60])   # 30 absent (G4), no scarcity counter (G6)


class CancelReschedule(unittest.TestCase):
    def setUp(self):
        proposed = agent.propose_booking(_req(600), [])
        self.confirmed = agent.confirm_booking(proposed, {"origin": "member", "ref": "s1"}, [])

    def test_cancel_frees_slot(self):
        cancelled = agent.cancel_booking(self.confirmed)
        self.assertEqual(cancelled["status"], "cancelled")
        # a cancelled booking does not block availability
        self.assertTrue(agent.is_free(CAL, 600, 30, [cancelled]))

    def test_reschedule_to_free_slot(self):
        out = agent.reschedule_booking(self.confirmed, 720, 30, [self.confirmed],
                                       {"origin": "member", "ref": "s2"})
        self.assertTrue(out.get("rescheduled"))
        self.assertEqual(out["startEpochMin"], 720)

    def test_reschedule_excludes_own_slot(self):
        # rescheduling to (almost) the same window must not collide with itself
        out = agent.reschedule_booking(self.confirmed, 605, 30, [self.confirmed],
                                       {"origin": "member", "ref": "s2"})
        self.assertTrue(out.get("rescheduled"))

    def test_reschedule_into_conflict_refused(self):
        other = {"bookingId": "bk2", "status": "confirmed", "calendarDid": CAL,
                 "startEpochMin": 720, "durationMin": 30}
        out = agent.reschedule_booking(self.confirmed, 720, 30, [self.confirmed, other],
                                       {"origin": "member", "ref": "s2"})
        self.assertTrue(out["refused"])
        self.assertIn("G4", out["reason"])

    def test_reschedule_server_sig_refused(self):
        out = agent.reschedule_booking(self.confirmed, 720, 30, [self.confirmed],
                                       {"origin": "server", "ref": "x"})
        self.assertTrue(out["refused"])
        self.assertIn("G5", out["reason"])

    def test_reschedule_nonconfirmed_refused(self):
        proposed = agent.propose_booking(_req(900), [])
        out = agent.reschedule_booking(proposed, 960, 30, [], {"origin": "member", "ref": "s"})
        self.assertTrue(out["refused"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
