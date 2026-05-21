"""errors — PDS error hierarchy for etzhayyim_sdk.

All PDS XRPC errors inherit from PdsError. Import from here for clean exception
handling in application code:

    from etzhayyim_sdk.errors import PdsAuthError, PdsNotFoundError

ADR references:
  ADR-2605172000 — RW-free substrate hard rule (this package is the only seam)
  ADR-2605173000 — PDS endpoint: https://atproto.etzhayyim.com
"""

from __future__ import annotations


class PdsError(Exception):
    """Base class for all PDS XRPC errors.

    All etzhayyim_sdk.pds exceptions extend this class so callers can catch
    the entire hierarchy with a single ``except PdsError`` clause.
    """


class PdsAuthError(PdsError):
    """Raised on HTTP 401 (Unauthorized) or 403 (Forbidden) from the PDS.

    Typically indicates an invalid, expired, or missing DID-bound JWT in
    ``ETZHAYYIM_PDS_AUTH_TOKEN``.
    """


class PdsNotFoundError(PdsError):
    """Raised on HTTP 404 (Not Found) from the PDS.

    The requested AT URI / collection / rkey does not exist in the repo.
    """


class PdsServerError(PdsError):
    """Raised on HTTP 5xx responses from the PDS.

    The ``body`` attribute contains the raw response body text for debugging.
    """

    def __init__(self, status_code: int, body: str) -> None:
        self.status_code = status_code
        self.body = body
        super().__init__(f"PDS server error {status_code}: {body!r}")


class PdsNetworkError(PdsError):
    """Raised when the HTTP transport fails before a response is received.

    Wraps ``httpx.RequestError`` or ``httpx.TransportError`` subclasses.
    """

    def __init__(self, cause: Exception) -> None:
        self.cause = cause
        super().__init__(f"PDS network error: {cause}")


# ---------------------------------------------------------------------------
# IPFS error hierarchy (mirrors PdsError pattern)
# ---------------------------------------------------------------------------


class IpfsError(Exception):
    """Base class for all IPFS Kubo HTTP API errors.

    All etzhayyim_sdk.ipfs exceptions extend this class so callers can catch
    the entire hierarchy with a single ``except IpfsError`` clause.

    ADR-2605171800 Stage 3 — IPFS pinning via Kubo HTTP API on simeon.
    """


class IpfsNetworkError(IpfsError):
    """Raised when the HTTP transport fails before a Kubo response is received.

    Wraps ``httpx.HTTPError`` (connect / read / timeout errors).
    The ``cause`` attribute holds the original exception.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)


class IpfsServerError(IpfsError):
    """Raised on non-200 responses from the Kubo HTTP API, or when the
    response body does not confirm the expected operation (e.g. CID missing
    from ``Pins`` list).

    Attributes:
        status_code: HTTP status code, or 0 if the error is a body-level issue.
        body:        Raw response body text (first 200 chars).
    """

    def __init__(self, message: str, *, status_code: int = 0, body: str = "") -> None:
        self.status_code = status_code
        self.body = body
        super().__init__(message)


# ---------------------------------------------------------------------------
# MST subscribe error
# ---------------------------------------------------------------------------


class MstSubscribeError(Exception):
    """Raised by mst.subscribe after exceeding reconnect_max_attempts.

    The ``attempts`` attribute records how many reconnect attempts were made
    before giving up.

    ADR-2605215200 §1 KarmaHegemonObservationCell — subscribe error boundary.
    """

    def __init__(self, message: str, *, attempts: int = 0) -> None:
        self.attempts = attempts
        super().__init__(message)


# ---------------------------------------------------------------------------
# L2 error hierarchy (mirrors PdsError pattern)
# ---------------------------------------------------------------------------


class L2Error(Exception):
    """Base class for all Base L2 anchor errors.

    All etzhayyim_sdk.l2 exceptions extend this class so callers can catch
    the entire hierarchy with a single ``except L2Error`` clause.

    ADR-2605171800 Stage 4 — Base L2 anchor pipeline.
    """


class L2NetworkError(L2Error):
    """Raised when the HTTP transport fails before an RPC response is received.

    Wraps ``httpx.HTTPError`` (connect / read / timeout errors).
    """


class L2ServerError(L2Error):
    """Raised on non-200 HTTP responses from the JSON-RPC endpoint, or when
    the RPC body contains a top-level ``"error"`` field.

    Attributes:
        message: Human-readable error description.
    """


class L2ContractError(L2Error):
    """Raised when the anchor contract address is unset, placeholder
    (0x000…0), or when the contract reverts (e.g. AlreadyAnchored).

    Provision ``ETZHAYYIM_L2_CONTRACT_ADDRESS`` after Step 8 cutover deploy.
    """


class L2SigningError(L2Error):
    """Raised when the anchor private key is missing, invalid hex, or when
    the ``eth_account`` dependency is not installed.

    Provision ``ETZHAYYIM_L2_ANCHOR_KEY`` after Step 8 cutover.
    """


class L2VerificationError(L2Error):
    """Raised when a Merkle proof is structurally invalid or contains
    unparseable fields (e.g. missing keys, bad hex in sibling hash, invalid
    side indicator).

    Distinct from a *failed* verification (which returns ``False``): this
    error is for proofs that cannot be evaluated at all.

    ADR-2605171800 Stage 4 — L2 anchor proof verification.
    """


# ---------------------------------------------------------------------------
# LLM / inference error hierarchy (mirrors PdsError pattern)
# ---------------------------------------------------------------------------


class EtzhayyimSdkError(Exception):
    """Root base class for all etzhayyim SDK errors.

    Catch this to handle any SDK error uniformly.
    """


class LlmError(EtzhayyimSdkError):
    """Base class for all LLM / inference errors.

    All etzhayyim_sdk.llm exceptions extend this class so callers can catch
    the entire hierarchy with a single ``except LlmError`` clause.

    ADR-2605215000 — inference SSoT: LiteLLM @ 127.0.0.1:4000 OR EVO-X2 LAN
    @ 192.168.1.70:4000.
    """


class LlmNetworkError(LlmError):
    """Raised when the HTTP transport fails before a response is received.

    Wraps ``httpx.RequestError`` or ``httpx.TransportError`` subclasses.
    The ``cause`` attribute holds the original exception.
    """

    def __init__(self, cause: Exception) -> None:
        self.cause = cause
        super().__init__(f"LLM network error: {cause}")


class LlmServerError(LlmError):
    """Raised on HTTP 5xx responses from the LiteLLM gateway.

    The ``status_code`` and ``body`` attributes are available for debugging.
    """

    def __init__(self, status_code: int, body: str) -> None:
        self.status_code = status_code
        self.body = body
        super().__init__(f"LLM server error {status_code}: {body!r}")


class LlmAuthError(LlmError):
    """Raised on HTTP 401 (Unauthorized) or 403 (Forbidden) from the LiteLLM gateway.

    Typically indicates an invalid or missing ``ETZHAYYIM_LITELLM_KEY``.
    """


class LlmRateLimitError(LlmError):
    """Raised on HTTP 429 (Too Many Requests) from the LiteLLM gateway.

    Caller should back off before retrying.
    """


class LlmParseError(LlmError):
    """Raised when ``chat_json()`` or ``vision_json()`` cannot parse the
    assistant message content as valid JSON.

    The ``raw`` attribute contains the unparseable text for debugging.
    """

    def __init__(self, message: str, *, raw: str = "") -> None:
        self.raw = raw
        super().__init__(message)
