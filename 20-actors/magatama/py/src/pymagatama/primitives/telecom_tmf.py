"""telecom Phase 17 primitives — TM Forum Open APIs.

Eight BPMN service tasks covering the full TMF Open API suite:

  - telecom.tmf.product.offering   (TMF620 Product Catalog)
  - telecom.tmf.product.order      (TMF622 Product Ordering)
  - telecom.tmf.product.inventory  (TMF637 Product Inventory)
  - telecom.tmf.service.order      (TMF641 Service Ordering)
  - telecom.tmf.service.activate   (TMF640 Service Activation)
  - telecom.tmf.service.inventory  (TMF638 Service Inventory)
  - telecom.tmf.account.register   (TMF666 Account Management)  ← PII hashed
  - telecom.tmf.bill.issue         (TMF678 Customer Bill)

PII discipline (TMF666):
  partyName / partyContact / partyTaxId / billingAddress → sha256: hashed
  (sensitivity_ord=2 for account; bill rows are sensitivity_ord=2)
"""

from __future__ import annotations

import hashlib
import json
import secrets
from datetime import UTC, datetime
from typing import Any

from pymagatama.db_sync import sync_cursor


TELECOM_DID = "did:web:telecom.gftd.ai"
ACTOR_TAG = "sys.worker.telecom.tmf"

LIFECYCLE_STATUS_PRODUCT_OFFERING = {
    "In Study", "In Design", "In Test", "Active", "Launched",
    "Retired", "Obsolete", "Rejected",
}
LIFECYCLE_STATUS_PRODUCT_ORDER = {
    "acknowledged", "rejected", "pending", "held",
    "inProgress", "cancelled", "completed", "failed", "partial",
}
LIFECYCLE_STATUS_PRODUCT_INVENTORY = {
    "Created", "Pending Active", "Pending Terminate",
    "Active", "Suspended", "Terminated", "Aborted",
}
LIFECYCLE_STATUS_SERVICE_ORDER = {
    "acknowledged", "rejected", "pending", "held",
    "inProgress", "cancelled", "completed", "failed", "partial",
}
LIFECYCLE_STATUS_SERVICE_INVENTORY = {
    "feasibilityChecked", "designed", "reserved",
    "inactive", "active", "terminated",
}
ORDER_KINDS_PRODUCT = {"add", "modify", "suspend", "resume", "terminate"}
ORDER_KINDS_SERVICE = {"add", "modify", "delete", "noChange"}
CUSTOMER_KINDS = {"individual", "organization"}
ACCOUNT_KINDS = {"prepaid", "postpaid", "hybrid"}
PAYMENT_METHOD_KINDS = {"bankTransfer", "creditCard", "directDebit", "electronicCheck", "token"}
DELIVERY_CHANNELS = {"email", "post", "portal", "api"}
ACTIVATION_ACTIONS = {"activate", "deactivate", "configure", "test", "reconfigure"}


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _new_id(prefix: str, *parts: Any) -> str:
    if parts:
        digest = hashlib.sha256("|".join(str(p) for p in parts).encode()).hexdigest()[:24]
        return f"{prefix}_{digest}"
    return f"{prefix}_{secrets.token_hex(10)}"


def _vid(kind: str, key: str) -> str:
    return f"at://{TELECOM_DID}/ai.gftd.apps.telecom.{kind}/{key}"


def _hash_pii(value: str | None) -> str | None:
    if not value:
        return None
    return "sha256:" + hashlib.sha256(value.encode()).hexdigest()


def _join(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, (list, tuple)):
        items = [str(v).strip() for v in value if str(v).strip()]
        return ",".join(items) if items else None
    text = str(value).strip()
    return text or None


def _require(payload: dict[str, Any], fields: list[str]) -> None:
    missing = [f for f in fields if payload.get(f) in (None, "")]
    if missing:
        raise ValueError(f"Missing required fields: {missing}")


# ─── TMF620: publishProductOffering ──────────────────────────────────────────

def handle_publish_product_offering(payload: dict[str, Any]) -> dict[str, Any]:
    _require(payload, ["offeringId", "name", "lifecycleStatus"])

    offering_id = payload["offeringId"]
    lifecycle = payload["lifecycleStatus"]
    if lifecycle not in LIFECYCLE_STATUS_PRODUCT_OFFERING:
        lifecycle = "Active"

    observed_at = payload.get("observedAt") or _now_iso()
    vertex_id = _vid("productOffering", offering_id)

    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_telecom_tmf_product_offering (
              vertex_id, owner_did, offering_id, name, description,
              lifecycle_status, product_spec_id, category_ids, channel_ids,
              market_ids, price_ref, valid_from_at, valid_to_at,
              observed_at, status, created_at, sensitivity_ord,
              org_id, user_id, actor_id
            ) VALUES (
              %s, %s, %s, %s, %s,
              %s, %s, %s, %s,
              %s, %s, %s, %s,
              %s, %s, %s, %s,
              %s, %s, %s
            )
            """,
            (
                vertex_id, TELECOM_DID, offering_id,
                payload["name"], payload.get("description"),
                lifecycle, payload.get("productSpecId"),
                _join(payload.get("categoryIds")),
                _join(payload.get("channelIds")),
                _join(payload.get("marketIds")),
                payload.get("priceRef"),
                payload.get("validFromAt"), payload.get("validToAt"),
                observed_at, "active", observed_at, 2,
                payload.get("callerDid", TELECOM_DID),
                payload.get("callerDid", TELECOM_DID),
                ACTOR_TAG,
            ),
        )

    return {"vertexId": vertex_id, "offeringId": offering_id, "status": "active"}


# ─── TMF622: submitProductOrder ──────────────────────────────────────────────

def handle_submit_product_order(payload: dict[str, Any]) -> dict[str, Any]:
    _require(payload, ["productOrderId", "accountId", "orderKind"])

    order_id = payload["productOrderId"]
    order_kind = payload["orderKind"]
    if order_kind not in ORDER_KINDS_PRODUCT:
        order_kind = "add"

    observed_at = payload.get("observedAt") or _now_iso()
    vertex_id = _vid("productOrder", order_id)

    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_telecom_tmf_product_order (
              vertex_id, owner_did, product_order_id, account_id, order_kind,
              offering_id, product_id, order_item_hash, order_item_ref,
              requested_start_at, requested_completion_at, priority, channel_id,
              observed_at, status, created_at, sensitivity_ord,
              org_id, user_id, actor_id
            ) VALUES (
              %s, %s, %s, %s, %s,
              %s, %s, %s, %s,
              %s, %s, %s, %s,
              %s, %s, %s, %s,
              %s, %s, %s
            )
            """,
            (
                vertex_id, TELECOM_DID, order_id,
                payload["accountId"], order_kind,
                payload.get("offeringId"), payload.get("productId"),
                payload.get("orderItemHash"), payload.get("orderItemRef"),
                payload.get("requestedStartAt"), payload.get("requestedCompletionAt"),
                payload.get("priority"), payload.get("channelId"),
                observed_at, "acknowledged", observed_at, 2,
                payload.get("callerDid", TELECOM_DID),
                payload.get("callerDid", TELECOM_DID),
                ACTOR_TAG,
            ),
        )

    return {"vertexId": vertex_id, "productOrderId": order_id, "status": "acknowledged"}


# ─── TMF637: recordProductInventoryItem ──────────────────────────────────────

def handle_record_product_inventory_item(payload: dict[str, Any]) -> dict[str, Any]:
    _require(payload, ["recordId", "productId", "accountId", "lifecycleStatus"])

    record_id = payload["recordId"]
    lifecycle = payload["lifecycleStatus"]
    if lifecycle not in LIFECYCLE_STATUS_PRODUCT_INVENTORY:
        lifecycle = "Active"

    observed_at = payload.get("observedAt") or _now_iso()
    vertex_id = _vid("productInventory", record_id)

    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_telecom_tmf_product_inventory (
              vertex_id, owner_did, record_id, product_id, account_id,
              offering_id, product_order_id, lifecycle_status,
              started_at, terminated_at, observed_at, status, created_at,
              sensitivity_ord, org_id, user_id, actor_id
            ) VALUES (
              %s, %s, %s, %s, %s,
              %s, %s, %s,
              %s, %s, %s, %s, %s,
              %s, %s, %s, %s
            )
            """,
            (
                vertex_id, TELECOM_DID, record_id,
                payload["productId"], payload["accountId"],
                payload.get("offeringId"), payload.get("productOrderId"),
                lifecycle,
                payload.get("startedAt"), payload.get("terminatedAt"),
                observed_at, "recorded", observed_at,
                2,
                payload.get("callerDid", TELECOM_DID),
                payload.get("callerDid", TELECOM_DID),
                ACTOR_TAG,
            ),
        )

    return {"vertexId": vertex_id, "recordId": record_id, "status": "recorded"}


# ─── TMF641: submitServiceOrder ──────────────────────────────────────────────

def handle_submit_service_order(payload: dict[str, Any]) -> dict[str, Any]:
    _require(payload, ["serviceOrderId", "productOrderId", "orderKind"])

    svc_order_id = payload["serviceOrderId"]
    order_kind = payload["orderKind"]
    if order_kind not in ORDER_KINDS_SERVICE:
        order_kind = "add"

    observed_at = payload.get("observedAt") or _now_iso()
    vertex_id = _vid("serviceOrder", svc_order_id)

    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_telecom_tmf_service_order (
              vertex_id, owner_did, service_order_id, product_order_id,
              product_id, service_spec, order_kind, order_item_hash, order_item_ref,
              requested_start_at, requested_completion_at,
              observed_at, status, created_at, sensitivity_ord,
              org_id, user_id, actor_id
            ) VALUES (
              %s, %s, %s, %s,
              %s, %s, %s, %s, %s,
              %s, %s,
              %s, %s, %s, %s,
              %s, %s, %s
            )
            """,
            (
                vertex_id, TELECOM_DID, svc_order_id,
                payload["productOrderId"],
                payload.get("productId"), payload.get("serviceSpec"),
                order_kind, payload.get("orderItemHash"), payload.get("orderItemRef"),
                payload.get("requestedStartAt"), payload.get("requestedCompletionAt"),
                observed_at, "acknowledged", observed_at, 2,
                payload.get("callerDid", TELECOM_DID),
                payload.get("callerDid", TELECOM_DID),
                ACTOR_TAG,
            ),
        )

    return {"vertexId": vertex_id, "serviceOrderId": svc_order_id, "status": "acknowledged"}


# ─── TMF640: activateServiceInstance ─────────────────────────────────────────

def handle_activate_service_instance(payload: dict[str, Any]) -> dict[str, Any]:
    _require(payload, ["activationId", "serviceOrderId", "serviceInstanceKind", "action"])

    act_id = payload["activationId"]
    action = payload["action"]
    if action not in ACTIVATION_ACTIONS:
        action = "activate"

    observed_at = payload.get("observedAt") or _now_iso()
    vertex_id = _vid("serviceActivation", act_id)

    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_telecom_tmf_service_activation (
              vertex_id, owner_did, activation_id, service_order_id,
              service_instance_kind, service_instance_vid, action,
              configuration_hash, configuration_ref,
              observed_at, status, created_at, sensitivity_ord,
              org_id, user_id, actor_id
            ) VALUES (
              %s, %s, %s, %s,
              %s, %s, %s,
              %s, %s,
              %s, %s, %s, %s,
              %s, %s, %s
            )
            """,
            (
                vertex_id, TELECOM_DID, act_id,
                payload["serviceOrderId"],
                payload["serviceInstanceKind"],
                payload.get("serviceInstanceVid"),
                action,
                payload.get("configurationHash"),
                payload.get("configurationRef"),
                observed_at, "completed", observed_at, 2,
                payload.get("callerDid", TELECOM_DID),
                payload.get("callerDid", TELECOM_DID),
                ACTOR_TAG,
            ),
        )

    return {"vertexId": vertex_id, "activationId": act_id, "status": "completed"}


# ─── TMF638: recordServiceInventoryItem ──────────────────────────────────────

def handle_record_service_inventory_item(payload: dict[str, Any]) -> dict[str, Any]:
    _require(payload, ["recordId", "serviceInstanceKind", "lifecycleStatus"])

    record_id = payload["recordId"]
    lifecycle = payload["lifecycleStatus"]
    if lifecycle not in LIFECYCLE_STATUS_SERVICE_INVENTORY:
        lifecycle = "active"

    observed_at = payload.get("observedAt") or _now_iso()
    vertex_id = _vid("serviceInventory", record_id)

    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_telecom_tmf_service_inventory (
              vertex_id, owner_did, record_id, service_instance_kind,
              service_instance_vid, product_id, service_order_id,
              lifecycle_status, operational_state, started_at,
              observed_at, status, created_at, sensitivity_ord,
              org_id, user_id, actor_id
            ) VALUES (
              %s, %s, %s, %s,
              %s, %s, %s,
              %s, %s, %s,
              %s, %s, %s, %s,
              %s, %s, %s
            )
            """,
            (
                vertex_id, TELECOM_DID, record_id,
                payload["serviceInstanceKind"],
                payload.get("serviceInstanceVid"),
                payload.get("productId"), payload.get("serviceOrderId"),
                lifecycle, payload.get("operationalState"),
                payload.get("startedAt"),
                observed_at, "recorded", observed_at, 2,
                payload.get("callerDid", TELECOM_DID),
                payload.get("callerDid", TELECOM_DID),
                ACTOR_TAG,
            ),
        )

    return {"vertexId": vertex_id, "recordId": record_id, "status": "recorded"}


# ─── TMF666: registerCustomerAccount ─────────────────────────────────────────

def handle_register_customer_account(payload: dict[str, Any]) -> dict[str, Any]:
    _require(payload, ["accountId", "customerKind", "accountKind"])

    account_id = payload["accountId"]
    customer_kind = payload["customerKind"]
    if customer_kind not in CUSTOMER_KINDS:
        customer_kind = "individual"
    account_kind = payload["accountKind"]
    if account_kind not in ACCOUNT_KINDS:
        account_kind = "postpaid"

    payment_kind = payload.get("paymentMethodKind")
    if payment_kind and payment_kind not in PAYMENT_METHOD_KINDS:
        payment_kind = None

    observed_at = payload.get("observedAt") or _now_iso()
    vertex_id = _vid("customerAccount", account_id)

    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_telecom_tmf_customer_account (
              vertex_id, owner_did, account_id, customer_kind, account_kind,
              party_name, party_contact, party_tax_id, billing_address,
              currency, payment_method_kind, payment_method_ref,
              parent_subscriber_id, jurisdiction,
              observed_at, status, created_at, sensitivity_ord,
              org_id, user_id, actor_id
            ) VALUES (
              %s, %s, %s, %s, %s,
              %s, %s, %s, %s,
              %s, %s, %s,
              %s, %s,
              %s, %s, %s, %s,
              %s, %s, %s
            )
            """,
            (
                vertex_id, TELECOM_DID, account_id,
                customer_kind, account_kind,
                _hash_pii(payload.get("partyName")),
                _hash_pii(payload.get("partyContact")),
                _hash_pii(payload.get("partyTaxId")),
                _hash_pii(payload.get("billingAddress")),
                payload.get("currency"), payment_kind,
                payload.get("paymentMethodRef"),
                payload.get("parentSubscriberId"),
                payload.get("jurisdiction"),
                observed_at, "active", observed_at, 2,
                payload.get("callerDid", TELECOM_DID),
                payload.get("callerDid", TELECOM_DID),
                ACTOR_TAG,
            ),
        )

    return {"vertexId": vertex_id, "accountId": account_id, "status": "active"}


# ─── TMF678: issueCustomerBill ────────────────────────────────────────────────

def handle_issue_customer_bill(payload: dict[str, Any]) -> dict[str, Any]:
    _require(payload, ["billId", "accountId", "periodStart", "periodEnd"])

    bill_id = payload["billId"]
    delivery = payload.get("deliveryChannel")
    if delivery and delivery not in DELIVERY_CHANNELS:
        delivery = "portal"

    # total_amount is computed by the downstream billing engine; default 0.0 for skeleton
    total_amount: float = payload.get("totalAmount", 0.0)
    created_at = _now_iso()
    vertex_id = _vid("customerBill", bill_id)

    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_telecom_tmf_customer_bill (
              vertex_id, owner_did, bill_id, account_id, period_start, period_end,
              currency, source_invoice_vids, due_at, delivery_channel,
              bill_document_ref, total_amount, status, created_at,
              sensitivity_ord, org_id, user_id, actor_id
            ) VALUES (
              %s, %s, %s, %s, %s, %s,
              %s, %s, %s, %s,
              %s, %s, %s, %s,
              %s, %s, %s, %s
            )
            """,
            (
                vertex_id, TELECOM_DID, bill_id,
                payload["accountId"],
                payload["periodStart"], payload["periodEnd"],
                payload.get("currency"),
                _join(payload.get("sourceInvoiceVids")),
                payload.get("dueAt"), delivery,
                payload.get("billDocumentRef"),
                total_amount, "issued", created_at,
                2,
                payload.get("callerDid", TELECOM_DID),
                payload.get("callerDid", TELECOM_DID),
                ACTOR_TAG,
            ),
        )

    return {
        "vertexId": vertex_id,
        "billId": bill_id,
        "totalAmount": total_amount,
        "status": "issued",
    }


# ─── Worker registration ──────────────────────────────────────────────────────

def register(worker: Any, timeout_ms: int = 30_000) -> None:
    @worker.task(task_type="telecom.tmf.product.offering", timeout_ms=timeout_ms)
    def _offering(payload: dict) -> dict:
        return handle_publish_product_offering(payload)

    @worker.task(task_type="telecom.tmf.product.order", timeout_ms=timeout_ms)
    def _product_order(payload: dict) -> dict:
        return handle_submit_product_order(payload)

    @worker.task(task_type="telecom.tmf.product.inventory", timeout_ms=timeout_ms)
    def _product_inventory(payload: dict) -> dict:
        return handle_record_product_inventory_item(payload)

    @worker.task(task_type="telecom.tmf.service.order", timeout_ms=timeout_ms)
    def _service_order(payload: dict) -> dict:
        return handle_submit_service_order(payload)

    @worker.task(task_type="telecom.tmf.service.activate", timeout_ms=timeout_ms)
    def _activate(payload: dict) -> dict:
        return handle_activate_service_instance(payload)

    @worker.task(task_type="telecom.tmf.service.inventory", timeout_ms=timeout_ms)
    def _service_inventory(payload: dict) -> dict:
        return handle_record_service_inventory_item(payload)

    @worker.task(task_type="telecom.tmf.account.register", timeout_ms=timeout_ms)
    def _account(payload: dict) -> dict:
        return handle_register_customer_account(payload)

    @worker.task(task_type="telecom.tmf.bill.issue", timeout_ms=60_000)
    def _bill(payload: dict) -> dict:
        return handle_issue_customer_bill(payload)
