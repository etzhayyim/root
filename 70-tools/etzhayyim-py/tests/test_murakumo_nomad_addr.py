"""Unit tests for etzhayyim.murakumo_cmd Nomad address resolution.

Regression cover for the sweep recorded in ADR-2608122600: a default endpoint
the workspace does not authoritatively own, sitting on a path that transmits a
credential.

``_resolve_nomad_addr`` used to fall back to ``http://benjamin.local:4646``.
``benjamin`` is a real murakumo mac-mini and ``.local`` is the mDNS namespace
(RFC 6762), so any host on the same link can claim the name by answering the
multicast query first.  ``_run_nomad`` hands the nomad CLI the caller's whole
environment, and the CLI sends ``$NOMAD_TOKEN`` as ``X-Nomad-Token`` to whatever
``NOMAD_ADDR`` names — so the fallback could hand an operator's Nomad token to
whoever replied fastest on the LAN.

Two kinds of test live here, and the distinction is the point:

* The **address** tests fail before the fix and pass after it.  They are the
  security regression cover.
* The **environment-inheritance** tests pass both before and after.  They are
  the positive control, and they are deliberately written to FAIL if someone
  "hardens" this later by narrowing what ``_run_nomad`` passes to the child.
  Narrowing it would break the documented way to drive Nomad (NOMAD_TOKEN for
  ACLs, NOMAD_CACERT / NOMAD_CLIENT_CERT for mTLS, NOMAD_NAMESPACE,
  NOMAD_REGION) while closing nothing: any allowlist that kept the tool usable
  would still have to carry NOMAD_TOKEN, and the unauthenticated urllib paths
  (_nomad_node_id, _nomad_alloc_id, `fleet watch`) never touch the environment
  at all.  The address was the defect; the inheritance is correct behaviour.

No real subprocess is executed and no network call is made.
"""

from __future__ import annotations

from unittest.mock import patch

import click
import pytest

from etzhayyim.murakumo_cmd import _resolve_nomad_addr, _run_nomad


# ─── the address: these FAIL before the fix ───────────────────────────────────

class TestNomadAddrRequiresExplicitValue:
    def test_unset_raises_instead_of_guessing_a_host(self, monkeypatch):
        monkeypatch.delenv("NOMAD_ADDR", raising=False)
        with pytest.raises(click.ClickException) as excinfo:
            _resolve_nomad_addr()
        assert "NOMAD_ADDR" in str(excinfo.value)

    def test_unset_never_returns_an_mdns_host(self, monkeypatch):
        """The specific regression: no .local fallback, by any route."""
        monkeypatch.delenv("NOMAD_ADDR", raising=False)
        try:
            resolved = _resolve_nomad_addr()
        except click.ClickException:
            return  # failing closed is the whole point
        pytest.fail(f"resolved to {resolved!r} with NOMAD_ADDR unset")

    def test_blank_is_treated_as_unset(self, monkeypatch):
        """'   ' must not become the base of '   /v1/nodes'."""
        monkeypatch.setenv("NOMAD_ADDR", "   ")
        with pytest.raises(click.ClickException):
            _resolve_nomad_addr()

    def test_no_nomad_invoked_when_address_is_missing(self, monkeypatch):
        """The credential path must not open: nomad is never exec'd."""
        monkeypatch.delenv("NOMAD_ADDR", raising=False)
        monkeypatch.setenv("NOMAD_TOKEN", "secret-token-must-not-travel")
        with patch("shutil.which", return_value="/usr/local/bin/nomad"), \
                patch("subprocess.run") as run:
            with pytest.raises(click.ClickException):
                _run_nomad("node", "status")
        run.assert_not_called()


# ─── the address: honouring an operator's choice ──────────────────────────────

class TestNomadAddrHonoursTheOperator:
    def test_env_value_is_used(self, monkeypatch):
        monkeypatch.setenv("NOMAD_ADDR", "http://nomad.internal:4646")
        assert _resolve_nomad_addr() == "http://nomad.internal:4646"

    def test_trailing_slashes_stripped(self, monkeypatch):
        """Callers interpolate f'{addr}/v1/nodes'."""
        monkeypatch.setenv("NOMAD_ADDR", "http://nomad.internal:4646///")
        assert _resolve_nomad_addr() == "http://nomad.internal:4646"

    def test_surrounding_whitespace_stripped(self, monkeypatch):
        monkeypatch.setenv("NOMAD_ADDR", "  http://nomad.internal:4646  ")
        assert _resolve_nomad_addr() == "http://nomad.internal:4646"


# ─── positive control: passes before AND after the fix ────────────────────────

class TestRunNomadStillInheritsTheEnvironment:
    """Guards the decision, not just the code.

    If a later change narrows _run_nomad's child environment, these fail —
    which is the intended alarm, not an inconvenience.
    """

    def test_child_env_carries_the_operator_nomad_token(self, monkeypatch):
        monkeypatch.setenv("NOMAD_ADDR", "http://nomad.internal:4646")
        monkeypatch.setenv("NOMAD_TOKEN", "operator-token")
        with patch("shutil.which", return_value="/usr/local/bin/nomad"), \
                patch("subprocess.run") as run:
            run.return_value.returncode = 0
            _run_nomad("node", "status")
        child_env = run.call_args.kwargs["env"]
        assert child_env["NOMAD_TOKEN"] == "operator-token"

    def test_child_env_carries_tls_and_namespace_vars(self, monkeypatch):
        monkeypatch.setenv("NOMAD_ADDR", "http://nomad.internal:4646")
        monkeypatch.setenv("NOMAD_CACERT", "/etc/nomad/ca.pem")
        monkeypatch.setenv("NOMAD_NAMESPACE", "murakumo")
        with patch("shutil.which", return_value="/usr/local/bin/nomad"), \
                patch("subprocess.run") as run:
            run.return_value.returncode = 0
            _run_nomad("job", "status")
        child_env = run.call_args.kwargs["env"]
        assert child_env["NOMAD_CACERT"] == "/etc/nomad/ca.pem"
        assert child_env["NOMAD_NAMESPACE"] == "murakumo"

    def test_argv_unchanged_and_address_injected(self, monkeypatch):
        monkeypatch.setenv("NOMAD_ADDR", "http://nomad.internal:4646")
        monkeypatch.setenv("PATH", "/host/bin")
        with patch("shutil.which", return_value="/usr/local/bin/nomad"), \
                patch("subprocess.run") as run:
            run.return_value.returncode = 0
            _run_nomad("node", "drain", "-enable", "abc123")
        argv = run.call_args.args[0]
        assert argv == ["/usr/local/bin/nomad", "node", "drain", "-enable", "abc123"]
        child_env = run.call_args.kwargs["env"]
        assert child_env["NOMAD_ADDR"] == "http://nomad.internal:4646"
        # The child env is the caller's, not a hand-built allowlist.
        assert child_env["PATH"] == "/host/bin"
