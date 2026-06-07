"""ISO 20022 payment-message domain model (frozen dataclasses).

A cleanroom object model of the three message definitions kawase-yui needs
at its interop/ingress boundary (CLAUDE.md: "MST = ingress/interop wire" —
here the wire is the global ISO 20022 banking network):

- **pain.001** — ``CustomerCreditTransferInitiation`` (a party instructs
  its agent to make a credit transfer; the *ingress* of a real-world
  transfer into the kotoba Datom log).
- **pacs.008** — ``FIToFICustomerCreditTransfer`` (the inter-bank leg; the
  message SWIFT CBPR+ carries between financial institutions).
- **pacs.002** — ``FIToFIPaymentStatusReport`` (per-hop acceptance /
  rejection / pending acknowledgement).

The element names mirror the official ISO 20022 message components
(``GrpHdr`` / ``CdtTrfTxInf`` / ``PmtId`` / ``IntrBkSttlmAmt`` …) so the
codec in :mod:`kotoba_iso20022.codec` is a faithful, auditable mapping.

These dataclasses are pure data — building/parsing XML lives in the codec,
validation in :mod:`kotoba_iso20022.validate`, and the kotoba EAVT mapping
in :mod:`kotoba_iso20022.datoms`. Nothing here touches a network, a chain,
or money movement; it is format datafication only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Literal, Optional

__all__ = (
    "PostalAddress",
    "Party",
    "Account",
    "Agent",
    "Amount",
    "RemittanceInfo",
    "CreditTransferTransaction",
    "GroupHeader",
    "PaymentInstruction",
    "CustomerCreditTransferInitiation",
    "FIToFICustomerCreditTransfer",
    "TransactionStatus",
    "FIToFIPaymentStatusReport",
    "ChargeBearer",
    "SettlementMethod",
    "TxStatusCode",
    "CreditDebitCode",
    "BalanceType",
    "EntryStatus",
    "CashBalance",
    "StatementEntry",
    "AccountStatement",
    "BankToCustomerStatement",
    "AccountNotification",
    "BankToCustomerDebitCreditNotification",
    "BusinessApplicationHeader",
    "OriginalPaymentStatus",
    "CustomerPaymentStatusReport",
)

# ISO 20022 external code subsets actually used by the messages here.
ChargeBearer = Literal["DEBT", "CRED", "SHAR", "SLEV"]
SettlementMethod = Literal["INDA", "INGA", "COVE", "CLRG"]
# pacs.002 TransactionIndividualStatus (ISO external code set).
TxStatusCode = Literal["ACCP", "ACSP", "ACSC", "ACWC", "ACWP", "RJCT", "PDNG"]
# camt.05x CreditDebitCode + balance-type + entry-status code sets.
CreditDebitCode = Literal["CRDT", "DBIT"]
BalanceType = Literal["OPBD", "CLBD", "PRCD", "CLAV", "FWAV", "ITBD"]
EntryStatus = Literal["BOOK", "PDNG", "INFO"]


@dataclass(frozen=True)
class PostalAddress:
    """``PstlAdr`` — minimal structured address."""

    country: Optional[str] = None  # ISO 3166-1 alpha-2
    address_lines: tuple[str, ...] = ()


@dataclass(frozen=True)
class Party:
    """``Dbtr`` / ``Cdtr`` / ``InitgPty`` — an identified party."""

    name: str
    postal_address: Optional[PostalAddress] = None
    # ``Id`` — org BIC/LEI or private id; kept opaque at this layer.
    identifier: Optional[str] = None


@dataclass(frozen=True)
class Account:
    """``DbtrAcct`` / ``CdtrAcct`` — IBAN-or-other account identification."""

    iban: Optional[str] = None
    other_id: Optional[str] = None
    currency: Optional[str] = None  # ISO 4217

    def __post_init__(self) -> None:
        if not self.iban and not self.other_id:
            raise ValueError("Account needs either iban or other_id")


@dataclass(frozen=True)
class Agent:
    """``DbtrAgt`` / ``CdtrAgt`` — a financial institution (``FinInstnId``)."""

    bicfi: Optional[str] = None  # ISO 9362 BIC
    name: Optional[str] = None
    clearing_member_id: Optional[str] = None  # ClrSysMmbId/MmbId

    def __post_init__(self) -> None:
        if not self.bicfi and not self.clearing_member_id:
            raise ValueError("Agent needs bicfi or clearing_member_id")


@dataclass(frozen=True)
class Amount:
    """``ActiveCurrencyAndAmount`` — value + ISO 4217 currency."""

    value: Decimal
    currency: str


@dataclass(frozen=True)
class RemittanceInfo:
    """``RmtInf`` — unstructured remittance lines (``Ustrd``)."""

    unstructured: tuple[str, ...] = ()


@dataclass(frozen=True)
class CreditTransferTransaction:
    """``CdtTrfTxInf`` — one credit-transfer transaction.

    Shared shape across pain.001 and pacs.008. ``interbank_amount`` /
    ``interbank_settlement_date`` / ``charge_bearer`` / ``tx_id`` are the
    pacs.008 inter-bank fields; ``instructed_amount`` is the pain.001
    customer-instruction field. A given message populates the subset its
    definition requires (the codec enforces which).
    """

    end_to_end_id: str
    instruction_id: Optional[str] = None
    tx_id: Optional[str] = None          # pacs.008 TxId
    uetr: Optional[str] = None           # UUIDv4 end-to-end reference
    instructed_amount: Optional[Amount] = None      # pain.001 InstdAmt
    interbank_amount: Optional[Amount] = None        # pacs.008 IntrBkSttlmAmt
    interbank_settlement_date: Optional[str] = None  # IntrBkSttlmDt (ISO date)
    charge_bearer: Optional[ChargeBearer] = None
    debtor: Optional[Party] = None
    debtor_account: Optional[Account] = None
    debtor_agent: Optional[Agent] = None
    creditor_agent: Optional[Agent] = None
    creditor: Optional[Party] = None
    creditor_account: Optional[Account] = None
    remittance_info: Optional[RemittanceInfo] = None


@dataclass(frozen=True)
class GroupHeader:
    """``GrpHdr`` — message-level header common to all three definitions."""

    message_id: str
    creation_datetime: str  # ISO 8601 (CreDtTm)
    number_of_txs: int
    control_sum: Optional[Decimal] = None
    initiating_party: Optional[Party] = None        # pain.001 InitgPty
    settlement_method: Optional[SettlementMethod] = None  # pacs.008 SttlmInf


@dataclass(frozen=True)
class PaymentInstruction:
    """``PmtInf`` — a pain.001 payment-information block (PmtMtd=TRF)."""

    payment_info_id: str
    requested_execution_date: str  # ReqdExctnDt (ISO date)
    debtor: Party
    debtor_account: Account
    debtor_agent: Agent
    transactions: tuple[CreditTransferTransaction, ...]
    payment_method: Literal["TRF"] = "TRF"


@dataclass(frozen=True)
class CustomerCreditTransferInitiation:
    """pain.001 — ``CstmrCdtTrfInitn``."""

    group_header: GroupHeader
    payments: tuple[PaymentInstruction, ...]


@dataclass(frozen=True)
class FIToFICustomerCreditTransfer:
    """pacs.008 — ``FIToFICstmrCdtTrf``."""

    group_header: GroupHeader
    transactions: tuple[CreditTransferTransaction, ...]


@dataclass(frozen=True)
class TransactionStatus:
    """``TxInfAndSts`` — one transaction's status inside pacs.002."""

    status_id: str
    original_end_to_end_id: Optional[str] = None
    original_tx_id: Optional[str] = None
    original_uetr: Optional[str] = None
    transaction_status: TxStatusCode = "ACSP"
    status_reason_code: Optional[str] = None  # StsRsnInf/Rsn/Cd
    additional_info: tuple[str, ...] = ()


@dataclass(frozen=True)
class FIToFIPaymentStatusReport:
    """pacs.002 — ``FIToFIPmtStsRpt``."""

    group_header: GroupHeader
    original_message_id: str
    original_message_name_id: str  # e.g. "pacs.008.001.08"
    statuses: tuple[TransactionStatus, ...] = field(default_factory=tuple)


# --------------------------------------------------------------------------
# camt.053 / camt.054 — account reporting (reconciliation / off-ramp side)
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class CashBalance:
    """``Bal`` — a statement balance (opening / closing / available …)."""

    balance_type: BalanceType  # Tp/CdOrPrtry/Cd
    amount: Amount
    credit_debit: CreditDebitCode  # CdtDbtInd
    date: str  # Dt/Dt (ISO date)


@dataclass(frozen=True)
class StatementEntry:
    """``Ntry`` — one booked/pending entry, shared by camt.053 and camt.054."""

    amount: Amount
    credit_debit: CreditDebitCode  # CdtDbtInd
    status: EntryStatus  # Sts (BOOK / PDNG / INFO)
    booking_date: Optional[str] = None  # BookgDt/Dt
    value_date: Optional[str] = None  # ValDt/Dt
    account_servicer_reference: Optional[str] = None  # AcctSvcrRef
    bank_transaction_code: Optional[str] = None  # BkTxCd/Domn/Cd (kept opaque)
    end_to_end_id: Optional[str] = None  # NtryDtls/TxDtls/Refs/EndToEndId
    remittance_info: Optional[RemittanceInfo] = None


@dataclass(frozen=True)
class AccountStatement:
    """``Stmt`` — one account statement within camt.053."""

    statement_id: str
    creation_datetime: str
    account: Account
    balances: tuple[CashBalance, ...] = ()
    entries: tuple[StatementEntry, ...] = ()


@dataclass(frozen=True)
class BankToCustomerStatement:
    """camt.053 — ``BkToCstmrStmt``."""

    group_header: GroupHeader
    statements: tuple[AccountStatement, ...]


@dataclass(frozen=True)
class AccountNotification:
    """``Ntfctn`` — one account notification within camt.054."""

    notification_id: str
    creation_datetime: str
    account: Account
    entries: tuple[StatementEntry, ...] = ()


@dataclass(frozen=True)
class BankToCustomerDebitCreditNotification:
    """camt.054 — ``BkToCstmrDbtCdtNtfctn``."""

    group_header: GroupHeader
    notifications: tuple[AccountNotification, ...]


# --------------------------------------------------------------------------
# head.001 — Business Application Header (mandatory wrapper for CBPR+)
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class BusinessApplicationHeader:
    """head.001 — ``AppHdr``.

    The BAH that SWIFT CBPR+ mandates around every business message: it
    names the sending/receiving institutions, the message identity, and the
    definition the payload conforms to. ``message_definition`` MUST match
    the wrapped Document's message definition (a CBPR+ conformance rule the
    envelope codec enforces).
    """

    from_bic: str  # Fr/FIId/FinInstnId/BICFI
    to_bic: str  # To/FIId/FinInstnId/BICFI
    business_message_id: str  # BizMsgIdr
    message_definition: str  # MsgDefIdr, e.g. "pacs.008.001.08"
    creation_datetime: str  # CreDt
    business_service: Optional[str] = None  # BizSvc, e.g. "swift.cbprplus.02"


# --------------------------------------------------------------------------
# pain.002 — CustomerPaymentStatusReport (pain-side ack)
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class OriginalPaymentStatus:
    """``OrgnlPmtInfAndSts`` — statuses grouped by original PmtInfId."""

    original_payment_info_id: str
    statuses: tuple[TransactionStatus, ...] = ()


@dataclass(frozen=True)
class CustomerPaymentStatusReport:
    """pain.002 — ``CstmrPmtStsRpt``."""

    group_header: GroupHeader
    original_message_id: str
    original_message_name_id: str  # e.g. "pain.001.001.09"
    payment_statuses: tuple[OriginalPaymentStatus, ...] = ()
