"""kotoba_iso20022 — cleanroom ISO 20022 payment-message codec.

A dependency-free, charter-clean reimplementation of the three ISO 20022
message definitions the kawase-yui (為替結) cross-border actor needs at its
interop/ingress boundary, built purely from the *open published* standard
(no proprietary SWIFT SDK) — the same cleanroom posture warifu applied to
ISO 8583.

Why this exists: kawase-yui settles adherent-to-adherent over Base L2
stablecoins, but a member on/off-ramps through the real banking system,
which speaks ISO 20022 (the format SWIFT itself migrated to via CBPR+).
This module is the *traditional-finance ingress/interop wire* — it
translates between ISO 20022 XML and kotoba EAVT Datoms so a real bank
transfer becomes auditable, append-only kotoba history.

Boundaries (CRITICAL): this is a *format library* only. It does not open a
network connection, does not touch a chain, does not move money, does not
perform Travel-Rule / FATF passport KYC (the Adherent SBT remains the KYC
per kawase-yui G10). It is datafication of an open standard.

Public surface::

    from kotoba_iso20022 import (
        build_pacs008, parse_pacs008,
        build_pain001, parse_pain001,
        build_pacs002, parse_pacs002,
        to_datoms,
        validate_iban, validate_bic, validate_currency, validate_amount,
    )

Message definitions (version-parameterised; CBPR+/SEPA defaults):

- pain.001 — CustomerCreditTransferInitiation
- pacs.008 — FIToFICustomerCreditTransfer
- pacs.002 — FIToFIPaymentStatusReport
"""

from __future__ import annotations

from .codec import (
    DEFAULT_VERSIONS,
    Iso20022CodecError,
    build_pacs002,
    build_pacs008,
    build_pain001,
    parse_pacs002,
    parse_pacs008,
    parse_pain001,
    urn_for,
)
from .datoms import NS, Datom, to_datoms
from .validate import (
    InvalidAmount,
    InvalidBic,
    InvalidCurrency,
    InvalidIban,
    validate_amount,
    validate_bic,
    validate_currency,
    validate_iban,
)

__all__ = (
    # codec
    "build_pain001",
    "parse_pain001",
    "build_pacs008",
    "parse_pacs008",
    "build_pacs002",
    "parse_pacs002",
    "urn_for",
    "DEFAULT_VERSIONS",
    "Iso20022CodecError",
    # datoms
    "to_datoms",
    "Datom",
    "NS",
    # validators
    "validate_iban",
    "validate_bic",
    "validate_currency",
    "validate_amount",
    "InvalidIban",
    "InvalidBic",
    "InvalidCurrency",
    "InvalidAmount",
)

__version__ = "0.1.0"
