"""Tests for access_jwt_verify — the Stage-E keyless internal-trust verifier.

Run: python3 -m pytest 50-infra/k8s/bpmn-dispatcher/test_access_jwt_verify.py
 or: python3 50-infra/k8s/bpmn-dispatcher/test_access_jwt_verify.py

Uses a locally-generated RSA key as a stand-in for Cloudflare's signing key, so
the whole Access-JWT path is exercised offline (no network, no real CF tenant).
"""

from __future__ import annotations

import json
import time

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from jwt.algorithms import RSAAlgorithm

import access_jwt_verify as A

TEAM = "etzhayyim"
AUD = "test-access-aud-tag"
KID = "test-kid-1"


def _keypair():
    priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pub_jwk = json.loads(RSAAlgorithm.to_jwk(priv.public_key()))
    pub_jwk["kid"] = KID
    pub_jwk["alg"] = "RS256"
    return priv, {"keys": [pub_jwk]}


def _mint(priv, *, aud=AUD, iss=None, exp_in=300, kid=KID):
    iss = iss if iss is not None else A.access_issuer(TEAM)
    now = int(time.time())
    return jwt.encode(
        {"aud": aud, "iss": iss, "iat": now, "exp": now + exp_in, "sub": "worker"},
        priv,
        algorithm="RS256",
        headers={"kid": kid},
    )


def test_valid_access_jwt_passes():
    priv, jwks = _keypair()
    tok = _mint(priv)
    claims = A.verify_access_jwt(tok, team_domain=TEAM, expected_aud=AUD, jwks=jwks)
    assert claims["sub"] == "worker"


def test_wrong_aud_rejected():
    priv, jwks = _keypair()
    tok = _mint(priv, aud="some-other-app")
    try:
        A.verify_access_jwt(tok, team_domain=TEAM, expected_aud=AUD, jwks=jwks)
        assert False, "should have raised"
    except jwt.InvalidTokenError:
        pass


def test_wrong_issuer_rejected():
    priv, jwks = _keypair()
    tok = _mint(priv, iss="https://evil.cloudflareaccess.com")
    try:
        A.verify_access_jwt(tok, team_domain=TEAM, expected_aud=AUD, jwks=jwks)
        assert False, "should have raised"
    except jwt.InvalidTokenError:
        pass


def test_expired_rejected():
    priv, jwks = _keypair()
    tok = _mint(priv, exp_in=-3600)
    try:
        A.verify_access_jwt(tok, team_domain=TEAM, expected_aud=AUD, jwks=jwks)
        assert False, "should have raised"
    except jwt.InvalidTokenError:
        pass


def test_unknown_kid_rejected():
    priv, jwks = _keypair()
    tok = _mint(priv, kid="not-in-jwks")
    try:
        A.verify_access_jwt(tok, team_domain=TEAM, expected_aud=AUD, jwks=jwks)
        assert False, "should have raised"
    except jwt.InvalidTokenError:
        pass


def test_foreign_key_signature_rejected():
    priv, jwks = _keypair()
    other, _ = _keypair()  # different private key, same kid in jwks
    tok = _mint(other)
    try:
        A.verify_access_jwt(tok, team_domain=TEAM, expected_aud=AUD, jwks=jwks)
        assert False, "should have raised"
    except jwt.InvalidTokenError:
        pass


# ── authorize_request: dual-accept bridge ────────────────────────────────────


def test_authorize_off_mode_allows():
    ok, reason = A.authorize_request({}, mode="off")
    assert ok and reason == "auth-off"


def test_authorize_access_jwt_path():
    priv, jwks = _keypair()
    tok = _mint(priv)
    ok, reason = A.authorize_request(
        {"Cf-Access-Jwt-Assertion": tok},
        mode="strict",
        access_team_domain=TEAM,
        access_aud=AUD,
        get_jwks=lambda: jwks,
    )
    assert ok and reason == "access-jwt"


def test_authorize_legacy_hmac_bridge():
    ok, reason = A.authorize_request(
        {"x-internal-trust": "shhh"},
        mode="strict",
        internal_secret="shhh",
    )
    assert ok and reason == "legacy-hmac"


def test_authorize_bad_hmac_denied():
    ok, reason = A.authorize_request(
        {"x-internal-trust": "wrong"},
        mode="strict",
        internal_secret="shhh",
    )
    assert not ok


def test_authorize_prefers_jwt_then_falls_to_hmac():
    # JWT config present but no token in headers → falls through to HMAC bridge.
    _, jwks = _keypair()
    ok, reason = A.authorize_request(
        {"x-internal-trust": "shhh"},
        mode="strict",
        access_team_domain=TEAM,
        access_aud=AUD,
        get_jwks=lambda: jwks,
        internal_secret="shhh",
    )
    assert ok and reason == "legacy-hmac"


def test_authorize_strict_no_config_denies():
    ok, reason = A.authorize_request({}, mode="strict")
    assert not ok


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for fn in fns:
        fn()
        passed += 1
        print(f"✓ {fn.__name__}")
    print(f"\n{passed}/{len(fns)} passed")
