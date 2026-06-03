"""Regression coverage for the kotoba-os scan-cycle reference model.

Each test pins one ADR-2606031600 invariant so the WIT contract's central claim
("scan cycle = Datom transaction, replayable") cannot silently regress. Pure
stdlib + unittest; run: `python3 -m unittest -v` from this directory, or via the
runner `python3 test_scan_cycle_model.py`.
"""

import unittest

from scan_cycle_model import FaultedCycle, ScanHost


def _bang_bang_control(setpoint: int):
    """A trivial IEC-61131-3-style control program (the L5 guest's `scan`).
    If input ch0 (a process value) is below setpoint, command output ch10 ON,
    else OFF; record the decision as a Datom fact."""
    def scan(host: ScanHost, cycle: int) -> None:
        pv = host.read_input(0)
        on = pv < setpoint
        host.write_output(10, on)
        host.assert_fact(e="ctrl", a=":ctrl/command", v=("ON" if on else "OFF"))
    return scan


class ScanCycleSemantics(unittest.TestCase):

    def test_outputs_are_staged_not_applied_midcycle(self):
        """N3: a write_output inside the guest is staged; the bus only reflects
        it AFTER the host commits the cycle."""
        host = ScanHost()
        host.set_input(0, 5)

        def scan(host, cycle):
            host.write_output(10, True)
            # mid-cycle, the applied bus state must still be the pre-cycle value
            self.assertIsNone(host.applied_output(10))
        host.run_cycle(scan)
        self.assertTrue(host.applied_output(10))  # applied after commit

    def test_faulted_cycle_commits_nothing(self):
        """N3 atomicity: a FaultedCycle leaves outputs and the log untouched for
        that cycle (all-or-nothing)."""
        host = ScanHost()
        host.set_input(0, 5)

        def scan(host, cycle):
            host.write_output(10, True)
            host.assert_fact("ctrl", ":ctrl/command", "ON")
            raise FaultedCycle("sensor disagreement")
        report = host.run_cycle(scan)
        self.assertTrue(report["faulted"])
        self.assertEqual(report["outputs_staged"], 0)
        self.assertIsNone(host.applied_output(10))
        self.assertEqual(host.log, [])  # nothing durable from a faulted cycle

    def test_each_cycle_is_one_transaction_with_t_equal_cycle(self):
        """D3: every committed cycle appends Datoms all stamped T = cycle index."""
        host = ScanHost()
        scan = _bang_bang_control(setpoint=10)
        host.set_input(0, 3)   # below setpoint -> ON
        host.run_cycle(scan, duration_us=120)
        host.set_input(0, 20)  # above setpoint -> OFF
        host.run_cycle(scan, duration_us=131)

        t0 = [d for d in host.log if d.t == 0]
        t1 = [d for d in host.log if d.t == 1]
        self.assertTrue(t0 and all(d.t == 0 for d in t0))
        self.assertTrue(t1 and all(d.t == 1 for d in t1))
        # the command fact flipped between the two transactions
        cmd0 = next(d.v for d in t0 if d.a == ":ctrl/command")
        cmd1 = next(d.v for d in t1 if d.a == ":ctrl/command")
        self.assertEqual((cmd0, cmd1), ("ON", "OFF"))

    def test_as_of_reconstructs_machine_state(self):
        """Datomic as-of: state at any past cycle is recoverable from the log."""
        host = ScanHost()
        scan = _bang_bang_control(setpoint=10)
        host.set_input(0, 3); host.run_cycle(scan)   # cycle 0: ON
        host.set_input(0, 20); host.run_cycle(scan)  # cycle 1: OFF

        self.assertEqual(host.as_of(0)["ctrl|:ctrl/command"], "ON")
        self.assertEqual(host.as_of(1)["ctrl|:ctrl/command"], "OFF")
        # as_of(0) sees cycle 0's output (ON) and must NOT leak cycle 1's value
        self.assertEqual(host.as_of(0)["out:10|:io/output"], True)
        self.assertEqual(host.as_of(1)["out:10|:io/output"], False)

    def test_bus_state_is_a_pure_projection_of_the_log(self):
        """N7: applied outputs equal what replay derives from the Datom log alone,
        i.e. the bus holds no truth the log lacks."""
        host = ScanHost()
        scan = _bang_bang_control(setpoint=10)
        for pv in (3, 20, 8, 50):
            host.set_input(0, pv)
            host.run_cycle(scan)
        last_t = host.log[-1].t
        replayed = host.replay_outputs(last_t)
        live = {10: host.applied_output(10)}
        self.assertEqual(replayed, live)

    def test_log_is_append_only_and_immutable(self):
        """N7: Datoms are frozen; the log only grows."""
        host = ScanHost()
        host.set_input(0, 1)
        host.run_cycle(_bang_bang_control(5))
        n = len(host.log)
        with self.assertRaises(Exception):
            host.log[0].v = "tampered"  # frozen dataclass -> FrozenInstanceError
        host.set_input(0, 9)
        host.run_cycle(_bang_bang_control(5))
        self.assertGreater(len(host.log), n)  # only appended


if __name__ == "__main__":
    unittest.main(verbosity=2)
