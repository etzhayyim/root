#!/usr/bin/env python3
"""
Deepening-Phase generator for the 600 Clean Room Actors (ADR 260607).

Transitions actors from L1 (Scaffolded — 1 endpoint / 1 entity / boilerplate)
to L3 (Advanced — domain-differentiated multi-entity schema + full CRUD
endpoints with payload validation + Datomic query/transact).

Design (the honest part):
  The shallow-boilerplate critique in the ADR is answered NOT by emitting one
  generic CRUD template 600 times, but by a per-DOMAIN resource model. Each of
  the ~60 wave categories gets a hand-authored set of realistic resources
  (entities + fields). Marquee platforms additionally get a curated override
  with their real API resource names. So 600 actors materialize ~60 genuinely
  distinct domain models, not one template.

Generated per actor:
  schema/<platform>.kotoba   multi-entity namespace (>=5 entities)
  src/main.py                CRUD routes per entity (list/get/create/update/
                             delete) with required-field validation, plus a
                             /healthz probe, backed by DatomicClient.

Idempotent: safe to re-run; overwrites schema + main.py from the model.
Curated L2 hand-impls (salesforce, stripe) are upgraded in place via overrides.
"""

import os
import re
import glob
import sys

ACTORS_DIR = "20-actors"
TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS_DIR)

# ---------------------------------------------------------------------------
# 1. Domain resource models.  category-key -> { EntityName: {field: type} }
#    Types: string | integer | float | boolean | datetime
#    Every entity implicitly gets `id: string @unique` + `createdAt: datetime`.
# ---------------------------------------------------------------------------

def E(**fields):
    return fields


# Generic fallback model — used only when a platform's category is not (yet)
# mapped, so even an un-categorised actor reaches L3 (multi-entity + CRUD).
GENERIC_MODEL = {
    "Resource": E(name="string", type="string", status="string", externalId="string"),
    "Collection": E(name="string", description="string", itemCount="integer"),
    "Item": E(collectionId="string", name="string", value="string"),
    "Event": E(resourceId="string", type="string", payloadRef="string", occurredAt="datetime"),
    "Attachment": E(resourceId="string", name="string", contentRef="string", sizeBytes="integer"),
    "Webhook": E(event="string", url="string", active="boolean"),
}

CATEGORY_MODELS = {
    # ---- Wave 1 archetypes (well-known SaaS) ----------------------------
    "crm_sales": {
        "Account": E(name="string", domain="string", industry="string", ownerId="string", annualRevenue="float"),
        "Contact": E(accountId="string", firstName="string", lastName="string", email="string", phone="string"),
        "Lead": E(company="string", email="string", status="string", source="string", score="integer"),
        "Opportunity": E(accountId="string", name="string", stage="string", amount="float", closeDate="datetime"),
        "Activity": E(subjectId="string", type="string", subject="string", dueDate="datetime", done="boolean"),
        "Pipeline": E(name="string", stageOrder="string", ownerId="string"),
    },
    "erp_finance": {
        "GLAccount": E(code="string", name="string", type="string", currency="string", balance="float"),
        "JournalEntry": E(accountId="string", debit="float", credit="float", memo="string", postedAt="datetime"),
        "Invoice": E(customerId="string", number="string", total="float", currency="string", status="string"),
        "PurchaseOrder": E(vendorId="string", number="string", total="float", status="string"),
        "Vendor": E(name="string", taxId="string", terms="string", currency="string"),
        "CostCenter": E(code="string", name="string", ownerId="string"),
    },
    "iaas_cloud": {
        "Project": E(name="string", region="string", billingId="string"),
        "ComputeInstance": E(projectId="string", name="string", machineType="string", state="string", ipAddress="string"),
        "Volume": E(projectId="string", sizeGb="integer", type="string", attachedTo="string"),
        "Bucket": E(projectId="string", name="string", region="string", public="boolean"),
        "Network": E(projectId="string", cidr="string", region="string"),
        "IamRole": E(projectId="string", name="string", policy="string"),
    },
    "office_productivity": {
        "Workspace": E(name="string", ownerId="string", plan="string"),
        "Document": E(workspaceId="string", title="string", contentRef="string", ownerId="string"),
        "Folder": E(workspaceId="string", name="string", parentId="string"),
        "Comment": E(documentId="string", authorId="string", body="string"),
        "Permission": E(resourceId="string", principalId="string", role="string"),
        "User": E(email="string", displayName="string", status="string"),
    },
    "devops_ci": {
        "Repository": E(name="string", owner="string", defaultBranch="string", private="boolean"),
        "Pipeline": E(repoId="string", name="string", trigger="string"),
        "Build": E(pipelineId="string", number="integer", status="string", commitSha="string", durationMs="integer"),
        "Artifact": E(buildId="string", name="string", sizeBytes="integer", contentRef="string"),
        "Deployment": E(buildId="string", environment="string", status="string"),
        "Webhook": E(repoId="string", url="string", event="string", active="boolean"),
    },
    "ehr_health": {
        "Patient": E(mrn="string", givenName="string", familyName="string", birthDate="datetime", sex="string"),
        "Encounter": E(patientId="string", type="string", status="string", startedAt="datetime"),
        "Observation": E(patientId="string", code="string", value="string", unit="string", takenAt="datetime"),
        "Medication": E(patientId="string", code="string", dose="string", route="string", active="boolean"),
        "Practitioner": E(npi="string", givenName="string", familyName="string", specialty="string"),
        "Appointment": E(patientId="string", practitionerId="string", start="datetime", status="string"),
    },
    "ecommerce": {
        "Product": E(sku="string", title="string", price="float", currency="string", inventory="integer"),
        "Variant": E(productId="string", sku="string", price="float", optionValues="string"),
        "Order": E(customerId="string", number="string", total="float", currency="string", status="string"),
        "LineItem": E(orderId="string", productId="string", quantity="integer", unitPrice="float"),
        "Customer": E(email="string", firstName="string", lastName="string", phone="string"),
        "Collection": E(title="string", handle="string", published="boolean"),
    },
    "payments": {
        "Customer": E(email="string", name="string", phone="string", balance="integer"),
        "PaymentIntent": E(customerId="string", amount="integer", currency="string", status="string"),
        "Charge": E(customerId="string", paymentIntentId="string", amount="integer", currency="string", status="string"),
        "Refund": E(chargeId="string", amount="integer", reason="string", status="string"),
        "Payout": E(amount="integer", currency="string", arrivalDate="datetime", status="string"),
        "PaymentMethod": E(customerId="string", type="string", last4="string", brand="string"),
    },
    "data_analytics": {
        "Dataset": E(name="string", source="string", schemaRef="string", rowCount="integer"),
        "Query": E(datasetId="string", sql="string", ownerId="string"),
        "Dashboard": E(name="string", ownerId="string", layout="string"),
        "Report": E(dashboardId="string", name="string", schedule="string"),
        "Connection": E(name="string", type="string", host="string", active="boolean"),
        "Metric": E(datasetId="string", name="string", expression="string", unit="string"),
    },
    "design_tools": {
        "Project": E(name="string", ownerId="string", teamId="string"),
        "File": E(projectId="string", name="string", contentRef="string", version="integer"),
        "Frame": E(fileId="string", name="string", width="float", height="float"),
        "Component": E(fileId="string", name="string", description="string"),
        "Comment": E(fileId="string", authorId="string", body="string", resolved="boolean"),
        "Export": E(fileId="string", format="string", scale="float", contentRef="string"),
    },
    # ---- Wave 2 ---------------------------------------------------------
    "ai_ml": {
        "Model": E(name="string", family="string", contextWindow="integer", modality="string"),
        "Completion": E(modelId="string", prompt="string", output="string", tokens="integer"),
        "Embedding": E(modelId="string", input="string", dimensions="integer", vectorRef="string"),
        "FineTune": E(baseModelId="string", datasetId="string", status="string", epochs="integer"),
        "Dataset": E(name="string", rows="integer", contentRef="string"),
        "File": E(purpose="string", filename="string", sizeBytes="integer", contentRef="string"),
    },
    "martech": {
        "Campaign": E(name="string", channel="string", status="string", budget="float"),
        "Audience": E(name="string", size="integer", definition="string"),
        "Event": E(profileId="string", name="string", properties="string", occurredAt="datetime"),
        "Profile": E(email="string", externalId="string", traits="string"),
        "Message": E(campaignId="string", profileId="string", channel="string", status="string"),
        "Funnel": E(name="string", steps="string", conversionRate="float"),
    },
    "security_iam": {
        "Identity": E(username="string", email="string", status="string", mfaEnabled="boolean"),
        "Policy": E(name="string", effect="string", resources="string", actions="string"),
        "Detection": E(severity="string", rule="string", entityRef="string", detectedAt="datetime"),
        "Incident": E(title="string", severity="string", status="string", assignee="string"),
        "Asset": E(hostname="string", ipAddress="string", os="string", riskScore="float"),
        "Session": E(identityId="string", source="string", expiresAt="datetime"),
    },
    "hrtech": {
        "Employee": E(firstName="string", lastName="string", email="string", title="string", department="string"),
        "Candidate": E(firstName="string", lastName="string", email="string", stage="string"),
        "JobReq": E(title="string", department="string", status="string", openings="integer"),
        "PayrollRun": E(period="string", grossTotal="float", currency="string", status="string"),
        "TimeOff": E(employeeId="string", type="string", start="datetime", days="float", status="string"),
        "Review": E(employeeId="string", cycle="string", rating="float", reviewerId="string"),
    },
    "devtools_apm": {
        "Service": E(name="string", environment="string", language="string"),
        "Error": E(serviceId="string", message="string", culprit="string", count="integer"),
        "Trace": E(serviceId="string", operation="string", durationMs="integer", status="string"),
        "Metric": E(serviceId="string", name="string", value="float", unit="string"),
        "Alert": E(serviceId="string", condition="string", severity="string", active="boolean"),
        "Incident": E(title="string", status="string", severity="string", startedAt="datetime"),
    },
    "headless_ec_logistics": {
        "ContentEntry": E(modelName="string", title="string", locale="string", published="boolean"),
        "Product": E(sku="string", title="string", price="float", currency="string"),
        "Shipment": E(orderId="string", carrier="string", tracking="string", status="string"),
        "SearchIndex": E(name="string", recordCount="integer", primaryKey="string"),
        "Webhook": E(event="string", url="string", active="boolean"),
        "Order": E(number="string", total="float", currency="string", status="string"),
    },
    "fintech_web3": {
        "Account": E(holderId="string", currency="string", balance="float", status="string"),
        "Card": E(accountId="string", last4="string", network="string", state="string"),
        "Transaction": E(accountId="string", amount="float", currency="string", type="string", status="string"),
        "Order": E(symbol="string", side="string", quantity="float", price="float", status="string"),
        "Wallet": E(address="string", chain="string", balance="float"),
        "Ledger": E(accountId="string", debit="float", credit="float", memo="string"),
    },
    "comms_social": {
        "Channel": E(name="string", type="string", topic="string", memberCount="integer"),
        "Message": E(channelId="string", authorId="string", body="string", sentAt="datetime"),
        "User": E(handle="string", displayName="string", verified="boolean"),
        "Room": E(name="string", maxParticipants="integer", recording="boolean"),
        "Stream": E(roomId="string", status="string", bitrate="integer"),
        "Webhook": E(event="string", url="string", active="boolean"),
    },
    "cx_survey": {
        "Ticket": E(subject="string", requesterId="string", priority="string", status="string"),
        "Survey": E(title="string", type="string", status="string"),
        "Response": E(surveyId="string", respondentId="string", score="integer", submittedAt="datetime"),
        "Account": E(name="string", healthScore="float", arr="float"),
        "Conversation": E(accountId="string", channel="string", sentiment="float"),
        "Contact": E(email="string", firstName="string", lastName="string"),
    },
    "vertical_saas": {
        "Record": E(name="string", type="string", ownerId="string", status="string"),
        "Matter": E(clientId="string", title="string", status="string", openedAt="datetime"),
        "Contract": E(counterparty="string", value="float", status="string", signedAt="datetime"),
        "Course": E(title="string", term="string", enrollment="integer"),
        "Property": E(address="string", units="integer", value="float"),
        "Document": E(recordId="string", name="string", contentRef="string"),
    },
    # ---- Wave 3 ---------------------------------------------------------
    "lowcode_ipaas": {
        "Flow": E(name="string", trigger="string", status="string"),
        "Step": E(flowId="string", appName="string", action="string", position="integer"),
        "Connection": E(appName="string", authType="string", active="boolean"),
        "Run": E(flowId="string", status="string", durationMs="integer", startedAt="datetime"),
        "App": E(name="string", category="string"),
        "Webhook": E(flowId="string", url="string", active="boolean"),
    },
    "rpa": {
        "Bot": E(name="string", machine="string", status="string"),
        "Process": E(name="string", version="string", published="boolean"),
        "Job": E(processId="string", botId="string", status="string", startedAt="datetime"),
        "Queue": E(name="string", pending="integer", priority="string"),
        "Asset": E(name="string", type="string", valueRef="string"),
        "ProcessMining": E(name="string", caseCount="integer", variants="integer"),
    },
    "modern_data_stack": {
        "Connector": E(name="string", source="string", destination="string", status="string"),
        "Sync": E(connectorId="string", status="string", rows="integer", startedAt="datetime"),
        "Model": E(name="string", materialization="string", sql="string"),
        "Stream": E(name="string", partitions="integer", retentionMs="integer"),
        "Schema": E(name="string", database="string", tableCount="integer"),
        "Test": E(modelName="string", type="string", passed="boolean"),
    },
    "iot_edge": {
        "Device": E(serial="string", model="string", status="string", firmware="string"),
        "Telemetry": E(deviceId="string", metric="string", value="float", recordedAt="datetime"),
        "Gateway": E(name="string", location="string", deviceCount="integer"),
        "Command": E(deviceId="string", name="string", payload="string", status="string"),
        "Firmware": E(model="string", version="string", contentRef="string"),
        "Alert": E(deviceId="string", rule="string", severity="string"),
    },
    "regtech_privacy": {
        "DataSubject": E(email="string", jurisdiction="string", status="string"),
        "ConsentRecord": E(subjectId="string", purpose="string", granted="boolean", recordedAt="datetime"),
        "Request": E(subjectId="string", type="string", status="string", dueAt="datetime"),
        "Control": E(framework="string", name="string", status="string"),
        "Evidence": E(controlId="string", name="string", contentRef="string"),
        "Assessment": E(name="string", riskLevel="string", completedAt="datetime"),
    },
    "aec_govtech": {
        "Project": E(name="string", jurisdiction="string", status="string"),
        "Permit": E(projectId="string", type="string", number="string", status="string"),
        "Drawing": E(projectId="string", name="string", revision="string", contentRef="string"),
        "Inspection": E(permitId="string", type="string", result="string", inspectedAt="datetime"),
        "Asset": E(name="string", type="string", location="string", condition="string"),
        "ServiceRequest": E(citizenId="string", category="string", status="string"),
    },
    "media_video_cms": {
        "Asset": E(title="string", type="string", durationMs="integer", contentRef="string"),
        "Rendition": E(assetId="string", format="string", bitrate="integer", contentRef="string"),
        "Channel": E(name="string", description="string", public="boolean"),
        "Playlist": E(channelId="string", title="string", itemCount="integer"),
        "ContentEntry": E(modelName="string", title="string", locale="string", published="boolean"),
        "Experiment": E(name="string", variant="string", conversionRate="float"),
    },
    "event_npo_creator": {
        "Event": E(name="string", startsAt="datetime", venue="string", capacity="integer"),
        "Ticket": E(eventId="string", type="string", price="float", sold="integer"),
        "Attendee": E(eventId="string", email="string", checkedIn="boolean"),
        "Donor": E(email="string", name="string", lifetimeValue="float"),
        "Donation": E(donorId="string", amount="float", currency="string", recurring="boolean"),
        "Membership": E(memberId="string", tier="string", status="string"),
    },
    "core_banking_insurtech": {
        "Account": E(holderId="string", type="string", balance="float", currency="string", status="string"),
        "Loan": E(borrowerId="string", principal="float", rate="float", termMonths="integer", status="string"),
        "Policy": E(holderId="string", type="string", premium="float", coverage="float", status="string"),
        "Claim": E(policyId="string", amount="float", status="string", filedAt="datetime"),
        "Transaction": E(accountId="string", amount="float", type="string", postedAt="datetime"),
        "Customer": E(name="string", taxId="string", kycStatus="string"),
    },
    "devsecops_serverless": {
        "Service": E(name="string", runtime="string", region="string", status="string"),
        "Deployment": E(serviceId="string", version="string", status="string", deployedAt="datetime"),
        "Secret": E(name="string", scope="string", rotatedAt="datetime"),
        "ApiProxy": E(name="string", basePath="string", target="string", active="boolean"),
        "Database": E(name="string", engine="string", region="string", sizeGb="integer"),
        "Function": E(serviceId="string", name="string", memoryMb="integer", timeoutMs="integer"),
    },
    "enterprise_commerce_spend": {
        "Catalog": E(name="string", supplierId="string", itemCount="integer"),
        "Product": E(sku="string", title="string", price="float", currency="string"),
        "Requisition": E(requesterId="string", total="float", status="string"),
        "PurchaseOrder": E(supplierId="string", total="float", status="string"),
        "Supplier": E(name="string", taxId="string", rating="float"),
        "Invoice": E(supplierId="string", poId="string", total="float", status="string"),
    },
    # ---- Wave 4 (sovereign / gov) --------------------------------------
    "dpg_india_stack": {
        "Identity": E(externalId="string", jurisdiction="string", verified="boolean"),
        "Credential": E(identityId="string", type="string", issuer="string", issuedAt="datetime"),
        "Consent": E(identityId="string", purpose="string", granted="boolean", expiresAt="datetime"),
        "Transaction": E(identityId="string", type="string", amount="float", status="string"),
        "Document": E(identityId="string", type="string", contentRef="string"),
        "VerificationRequest": E(identityId="string", verifier="string", status="string"),
    },
    "us_federal": {
        "Filing": E(filerId="string", form="string", period="string", status="string"),
        "Entity": E(name="string", ein="string", jurisdiction="string"),
        "Dataset": E(name="string", agency="string", updatedAt="datetime"),
        "Application": E(applicantId="string", program="string", status="string"),
        "PublicRecord": E(recordType="string", jurisdiction="string", recordedAt="datetime"),
        "Notice": E(subjectId="string", type="string", issuedAt="datetime"),
    },
    "uk_eu_egov": {
        "Filing": E(filerId="string", scheme="string", period="string", status="string"),
        "Citizen": E(nationalId="string", jurisdiction="string"),
        "Service": E(name="string", department="string"),
        "Application": E(citizenId="string", serviceId="string", status="string"),
        "Dataset": E(name="string", publisher="string", updatedAt="datetime"),
        "Identity": E(citizenId="string", assuranceLevel="string", verified="boolean"),
    },
    "japan_apac_egov": {
        "Filing": E(filerId="string", form="string", fiscalYear="string", status="string"),
        "Corporation": E(name="string", corporateNumber="string", jurisdiction="string"),
        "Disclosure": E(corporationId="string", docType="string", submittedAt="datetime"),
        "Citizen": E(myNumber="string", municipality="string"),
        "Application": E(citizenId="string", procedure="string", status="string"),
        "Dataset": E(name="string", agency="string", updatedAt="datetime"),
    },
    "intl_orgs_central_banks": {
        "Indicator": E(code="string", name="string", unit="string", source="string"),
        "Observation": E(indicatorId="string", country="string", period="string", value="float"),
        "Country": E(iso3="string", name="string", region="string"),
        "Series": E(indicatorId="string", frequency="string", startPeriod="string"),
        "Report": E(title="string", publishedAt="datetime", contentRef="string"),
        "ExchangeRate": E(base="string", quote="string", rate="float", asOf="datetime"),
    },
    "open_banking_finreg": {
        "Account": E(holderId="string", iban="string", currency="string", balance="float"),
        "Consent": E(accountId="string", scope="string", status="string", expiresAt="datetime"),
        "Transaction": E(accountId="string", amount="float", currency="string", bookedAt="datetime"),
        "PaymentInitiation": E(debtorAccount="string", creditorAccount="string", amount="float", status="string"),
        "Institution": E(name="string", bic="string", country="string"),
        "Filing": E(institutionId="string", regime="string", period="string", status="string"),
    },
    "customs_trade_logistics": {
        "Declaration": E(declarantId="string", type="string", hsCode="string", status="string"),
        "Shipment": E(declarationId="string", carrier="string", origin="string", destination="string"),
        "Manifest": E(shipmentId="string", vessel="string", containerCount="integer"),
        "Tariff": E(hsCode="string", rate="float", jurisdiction="string"),
        "Permit": E(declarationId="string", type="string", status="string"),
        "Party": E(name="string", role="string", taxId="string"),
    },
    "public_health_env_ip": {
        "Application": E(applicantId="string", type="string", number="string", status="string"),
        "Grant": E(applicationId="string", number="string", grantedAt="datetime"),
        "Surveillance": E(disease="string", region="string", cases="integer", reportedAt="datetime"),
        "Measurement": E(station="string", parameter="string", value="float", measuredAt="datetime"),
        "Patent": E(applicantId="string", title="string", number="string", status="string"),
        "Trial": E(sponsor="string", phase="string", status="string"),
    },
    "public_safety_law": {
        "Case": E(number="string", jurisdiction="string", status="string", filedAt="datetime"),
        "Party": E(caseId="string", role="string", name="string"),
        "Document": E(caseId="string", type="string", contentRef="string"),
        "Incident": E(type="string", jurisdiction="string", occurredAt="datetime"),
        "Watchlist": E(name="string", program="string", entries="integer"),
        "Sanction": E(targetName="string", program="string", listedAt="datetime"),
    },
    "transit_smart_cities": {
        "Stop": E(code="string", name="string", lat="float", lon="float"),
        "Route": E(shortName="string", longName="string", mode="string"),
        "Trip": E(routeId="string", headsign="string", serviceId="string"),
        "Vehicle": E(routeId="string", label="string", lat="float", lon="float"),
        "ServiceAlert": E(routeId="string", cause="string", effect="string"),
        "Fare": E(routeId="string", price="float", currency="string"),
    },
    # ---- Wave 5 (deep systems) -----------------------------------------
    "fin_market_hft": {
        "Instrument": E(symbol="string", assetClass="string", exchange="string", currency="string"),
        "Quote": E(instrumentId="string", bid="float", ask="float", asOf="datetime"),
        "Order": E(instrumentId="string", side="string", quantity="float", price="float", status="string"),
        "Execution": E(orderId="string", quantity="float", price="float", executedAt="datetime"),
        "MarketData": E(instrumentId="string", open="float", high="float", low="float", close="float"),
        "Position": E(instrumentId="string", quantity="float", avgPrice="float"),
    },
    "web3_rpc": {
        "Block": E(number="integer", hash="string", chain="string", minedAt="datetime"),
        "Transaction": E(hash="string", fromAddr="string", toAddr="string", value="float", status="string"),
        "Contract": E(address="string", chain="string", abiRef="string"),
        "Account": E(address="string", chain="string", balance="float", nonce="integer"),
        "Event": E(contractAddr="string", name="string", blockNumber="integer", dataRef="string"),
        "Token": E(contractAddr="string", symbol="string", decimals="integer", standard="string"),
    },
    "telecom_satellite": {
        "Subscriber": E(imsi="string", msisdn="string", plan="string", status="string"),
        "Session": E(subscriberId="string", apn="string", startedAt="datetime", bytesUsed="integer"),
        "Message": E(fromAddr="string", toAddr="string", body="string", status="string"),
        "Number": E(e164="string", type="string", assignedTo="string"),
        "Terminal": E(serial="string", satellite="string", signalDb="float", online="boolean"),
        "UsageRecord": E(subscriberId="string", quantity="float", unit="string", ratedAt="datetime"),
    },
    "healthcare_fhir_bio": {
        "Patient": E(identifier="string", givenName="string", familyName="string", birthDate="datetime"),
        "Observation": E(patientId="string", code="string", value="string", unit="string"),
        "Condition": E(patientId="string", code="string", clinicalStatus="string"),
        "DiagnosticReport": E(patientId="string", code="string", status="string", issuedAt="datetime"),
        "Sequence": E(patientId="string", accession="string", referenceGenome="string"),
        "Specimen": E(patientId="string", type="string", collectedAt="datetime"),
    },
    "energy_grid_utilities": {
        "Meter": E(serial="string", type="string", location="string"),
        "Reading": E(meterId="string", value="float", unit="string", readAt="datetime"),
        "Node": E(name="string", region="string", voltageKv="float"),
        "LoadForecast": E(nodeId="string", period="string", megawatts="float"),
        "MarketBid": E(nodeId="string", price="float", megawatts="float", interval="string"),
        "Tag": E(nodeId="string", address="string", value="float", quality="string"),
    },
    "travel_aviation_hospitality": {
        "Flight": E(carrier="string", number="string", origin="string", destination="string", status="string"),
        "Booking": E(pnr="string", passengerName="string", status="string"),
        "Segment": E(bookingId="string", flightId="string", cabin="string", seat="string"),
        "Property": E(name="string", location="string", rooms="integer"),
        "Reservation": E(propertyId="string", guestName="string", checkIn="datetime", nights="integer"),
        "Fare": E(flightId="string", cabin="string", price="float", currency="string"),
    },
    "os_kernel": {
        "Process": E(pid="integer", command="string", state="string", uid="integer"),
        "Thread": E(pid="integer", tid="integer", state="string", priority="integer"),
        "FileDescriptor": E(pid="integer", fd="integer", path="string", mode="string"),
        "Syscall": E(name="string", number="integer", argCount="integer"),
        "MemoryRegion": E(pid="integer", startAddr="string", sizeBytes="integer", perms="string"),
        "Signal": E(pid="integer", number="integer", action="string"),
    },
    "ai_ml_infra_chips": {
        "Device": E(name="string", vendor="string", memoryGb="integer", index="integer"),
        "Kernel": E(deviceId="string", name="string", gridDim="string", blockDim="string"),
        "MemoryAlloc": E(deviceId="string", sizeBytes="integer", ptr="string"),
        "InferenceJob": E(modelRef="string", deviceId="string", status="string", latencyMs="float"),
        "Engine": E(name="string", precision="string", maxBatch="integer"),
        "Utilization": E(deviceId="string", gpuPct="float", memPct="float", sampledAt="datetime"),
    },
    "cyber_threat_intel": {
        "Indicator": E(type="string", value="string", confidence="integer", firstSeen="datetime"),
        "Vulnerability": E(cveId="string", cvss="float", description="string", published="datetime"),
        "ThreatActor": E(name="string", motivation="string", sophistication="string"),
        "Campaign": E(name="string", actorId="string", firstSeen="datetime"),
        "Host": E(ipAddress="string", asn="string", country="string", openPorts="string"),
        "Technique": E(attckId="string", tactic="string", name="string"),
    },
    "manufacturing_plm_robotics": {
        "Part": E(partNumber="string", name="string", revision="string", material="string"),
        "BOM": E(parentPartId="string", childPartId="string", quantity="integer"),
        "ChangeOrder": E(partId="string", number="string", status="string"),
        "WorkOrder": E(partId="string", quantity="integer", status="string"),
        "Robot": E(model="string", cellId="string", status="string", payloadKg="float"),
        "Program": E(robotId="string", name="string", cycleTimeMs="integer"),
    },
    # ---- Wave 6 (physical substrate) -----------------------------------
    "isa_quantum": {
        "Register": E(name="string", widthBits="integer", role="string"),
        "Instruction": E(mnemonic="string", opcode="string", operands="string"),
        "Qubit": E(index="integer", t1Us="float", t2Us="float", readoutError="float"),
        "Circuit": E(name="string", qubitCount="integer", depth="integer"),
        "Gate": E(circuitId="string", name="string", targets="string"),
        "Job": E(circuitId="string", shots="integer", status="string"),
    },
    "internet_routing": {
        "Prefix": E(cidr="string", originAsn="string", validity="string"),
        "Route": E(prefixId="string", nextHop="string", asPath="string"),
        "Peer": E(asn="string", ipAddress="string", state="string"),
        "Zone": E(name="string", serial="integer", refreshSec="integer"),
        "Record": E(zoneId="string", name="string", type="string", value="string"),
        "Tunnel": E(localAddr="string", remoteAddr="string", protocol="string", active="boolean"),
    },
    "mobility_auto_ev": {
        "Vehicle": E(vin="string", model="string", state="string", odometerKm="float"),
        "Signal": E(vehicleId="string", name="string", value="float", unit="string"),
        "ChargeSession": E(vehicleId="string", connectorId="string", energyKwh="float", status="string"),
        "Connector": E(stationId="string", standard="string", powerKw="float", status="string"),
        "Trip": E(vehicleId="string", distanceKm="float", startedAt="datetime"),
        "Command": E(vehicleId="string", name="string", status="string"),
    },
    "space_ocean_earth": {
        "Object": E(designator="string", type="string", source="string"),
        "Position": E(objectId="string", lat="float", lon="float", altitudeM="float", asOf="datetime"),
        "Observation": E(objectId="string", parameter="string", value="float", observedAt="datetime"),
        "Scene": E(satellite="string", sceneId="string", cloudCover="float", capturedAt="datetime"),
        "Float": E(wmoId="string", lat="float", lon="float", parkDepthM="float"),
        "Station": E(stationId="string", name="string", network="string"),
    },
    "agritech_food": {
        "Field": E(name="string", areaHa="float", crop="string", lat="float", lon="float"),
        "Operation": E(fieldId="string", type="string", date="datetime", rate="float"),
        "Reading": E(fieldId="string", parameter="string", value="float", recordedAt="datetime"),
        "Machine": E(model="string", serial="string", hoursUsed="float"),
        "Lot": E(productName="string", harvestId="string", quantity="float", traceCode="string"),
        "Imagery": E(fieldId="string", index="string", capturedAt="datetime", contentRef="string"),
    },
    "meta_knowledge_publishing": {
        "Work": E(doi="string", title="string", type="string", publishedAt="datetime"),
        "Author": E(orcid="string", givenName="string", familyName="string"),
        "Citation": E(workId="string", citedDoi="string"),
        "Standard": E(designation="string", title="string", organization="string", status="string"),
        "Record": E(accession="string", database="string", title="string"),
        "Subject": E(workId="string", term="string", scheme="string"),
    },
    "deep_logistics_supply": {
        "TradeItem": E(gtin="string", description="string", brand="string"),
        "Event": E(itemId="string", bizStep="string", disposition="string", recordedAt="datetime"),
        "Document": E(type="string", senderId="string", receiverId="string", status="string"),
        "Container": E(bicCode="string", type="string", status="string"),
        "Party": E(gln="string", name="string", role="string"),
        "Shipment": E(documentId="string", origin="string", destination="string", status="string"),
    },
    "materials_bio_chemical": {
        "Substance": E(casNumber="string", name="string", formula="string", molarMass="float"),
        "Compound": E(inchiKey="string", smiles="string", name="string"),
        "Structure": E(pdbId="string", title="string", method="string", resolution="float"),
        "Material": E(materialId="string", formula="string", bandGap="float"),
        "Standard": E(designation="string", title="string", organization="string"),
        "Property": E(substanceId="string", name="string", value="float", unit="string"),
    },
    "energy_commodities": {
        "Commodity": E(symbol="string", name="string", unit="string", exchange="string"),
        "Price": E(commodityId="string", value="float", currency="string", asOf="datetime"),
        "Contract": E(commodityId="string", expiry="string", lastPrice="float"),
        "Series": E(commodityId="string", frequency="string", source="string"),
        "Inventory": E(commodityId="string", region="string", quantity="float", reportedAt="datetime"),
        "Forecast": E(commodityId="string", period="string", value="float"),
    },
    "physical_benchmarks_classifications": {
        "Code": E(code="string", description="string", scheme="string", parentCode="string"),
        "Unit": E(symbol="string", name="string", quantity="string"),
        "Reference": E(name="string", value="float", uncertainty="float", unit="string"),
        "Mapping": E(fromCode="string", toScheme="string", toCode="string"),
        "Location": E(unLocode="string", name="string", country="string"),
        "Epoch": E(name="string", utcOffset="string", asOf="datetime"),
    },
    # ---- Waves 7-10 (regional super-apps, legacy substrate, frontier) ---
    "superapp": {
        "User": E(phone="string", displayName="string", kycStatus="string", walletId="string"),
        "Wallet": E(userId="string", currency="string", balance="float", status="string"),
        "Merchant": E(name="string", category="string", rating="float"),
        "RideOrder": E(userId="string", origin="string", destination="string", fare="float", status="string"),
        "FoodOrder": E(userId="string", merchantId="string", total="float", status="string"),
        "Payment": E(userId="string", amount="float", currency="string", method="string", status="string"),
    },
    "delivery_logistics": {
        "Order": E(customerId="string", merchantId="string", total="float", status="string"),
        "Courier": E(name="string", vehicle="string", lat="float", lon="float", online="boolean"),
        "Delivery": E(orderId="string", courierId="string", status="string", etaMin="integer"),
        "Merchant": E(name="string", cuisine="string", lat="float", lon="float"),
        "Route": E(deliveryId="string", distanceKm="float", durationMin="integer"),
        "Tracking": E(deliveryId="string", lat="float", lon="float", recordedAt="datetime"),
    },
    "ride_hailing": {
        "Driver": E(name="string", licensePlate="string", rating="float", online="boolean"),
        "Rider": E(name="string", phone="string", rating="float"),
        "Trip": E(riderId="string", driverId="string", origin="string", destination="string", status="string"),
        "Vehicle": E(driverId="string", make="string", model="string", plate="string"),
        "Fare": E(tripId="string", base="float", distanceKm="float", total="float", currency="string"),
        "Rating": E(tripId="string", byRole="string", score="integer", comment="string"),
    },
    "mainframe": {
        "Job": E(jcl="string", class_="string", owner="string", status="string"),
        "Dataset": E(name="string", dsorg="string", recfm="string", sizeTracks="integer"),
        "Region": E(name="string", type="string", maxTasks="integer"),
        "Subsystem": E(name="string", type="string", status="string"),
        "Transaction": E(code="string", program="string", regionId="string", status="string"),
        "Queue": E(name="string", depth="integer", maxDepth="integer"),
    },
    "scada": {
        "Tag": E(address="string", name="string", value="float", quality="string", unit="string"),
        "Device": E(name="string", protocol="string", ipAddress="string", online="boolean"),
        "Alarm": E(tagId="string", priority="string", state="string", raisedAt="datetime"),
        "Trend": E(tagId="string", sampleRateMs="integer", retentionDays="integer"),
        "ControlLoop": E(name="string", setpoint="float", processValue="float", mode="string"),
        "Batch": E(recipe="string", status="string", startedAt="datetime"),
    },
    "pharmacy_rx": {
        "Prescription": E(memberId="string", drugId="string", quantity="integer", refills="integer", status="string"),
        "Claim": E(prescriptionId="string", pharmacyId="string", amount="float", status="string"),
        "Pharmacy": E(npi="string", name="string", network="string"),
        "Drug": E(ndc="string", name="string", strength="string", form="string"),
        "Member": E(memberId="string", planId="string", groupId="string"),
        "PriorAuth": E(prescriptionId="string", status="string", decidedAt="datetime"),
    },
    "real_estate": {
        "Listing": E(propertyId="string", price="float", status="string", listedAt="datetime"),
        "Property": E(address="string", beds="integer", baths="float", sqft="integer", lat="float"),
        "Agent": E(name="string", license="string", brokerage="string"),
        "Transaction": E(listingId="string", buyerId="string", salePrice="float", closedAt="datetime"),
        "Lease": E(propertyId="string", tenantId="string", rent="float", startsAt="datetime"),
        "Tenant": E(name="string", email="string", phone="string"),
    },
    "gaming_backend": {
        "Player": E(handle="string", level="integer", xp="integer", region="string"),
        "Session": E(playerId="string", platform="string", startedAt="datetime", durationSec="integer"),
        "Match": E(mode="string", status="string", playerCount="integer"),
        "Leaderboard": E(name="string", metric="string", season="string"),
        "Inventory": E(playerId="string", itemId="string", quantity="integer"),
        "Achievement": E(playerId="string", code="string", unlockedAt="datetime"),
    },
    "legal_ediscovery": {
        "Matter": E(clientId="string", name="string", status="string", openedAt="datetime"),
        "Document": E(matterId="string", custodianId="string", contentRef="string", reviewStatus="string"),
        "Custodian": E(matterId="string", name="string", email="string"),
        "Review": E(documentId="string", reviewerId="string", coding="string"),
        "ProductionSet": E(matterId="string", name="string", documentCount="integer"),
        "LegalHold": E(matterId="string", custodianId="string", status="string", issuedAt="datetime"),
    },
    "bci_neuro": {
        "Device": E(model="string", channels="integer", samplingHz="integer", firmware="string"),
        "Session": E(deviceId="string", subjectRef="string", startedAt="datetime", durationSec="integer"),
        "Channel": E(deviceId="string", label="string", location="string", impedanceKohm="float"),
        "Signal": E(sessionId="string", channelLabel="string", band="string", dataRef="string"),
        "Event": E(sessionId="string", marker="string", offsetMs="integer"),
        "Calibration": E(deviceId="string", type="string", completedAt="datetime"),
    },
    "synbio": {
        "Strain": E(name="string", organism="string", genotype="string"),
        "Construct": E(name="string", vector="string", insertRef="string"),
        "Sequence": E(constructId="string", length="integer", checksum="string", dataRef="string"),
        "Assay": E(strainId="string", type="string", readout="string", value="float"),
        "Sample": E(strainId="string", barcode="string", volumeUl="float", location="string"),
        "Workflow": E(name="string", protocolRef="string", status="string"),
    },
    "xr_spatial": {
        "Anchor": E(sceneId="string", x="float", y="float", z="float", persistent="boolean"),
        "Scene": E(name="string", deviceId="string", meshRef="string"),
        "Mesh": E(sceneId="string", vertexCount="integer", contentRef="string"),
        "Session": E(deviceId="string", appId="string", startedAt="datetime"),
        "Asset": E(sceneId="string", type="string", contentRef="string"),
        "Device": E(model="string", platform="string", trackingMode="string"),
    },
    "drone_robotics": {
        "Drone": E(serial="string", model="string", batteryPct="float", status="string"),
        "Mission": E(droneId="string", type="string", status="string"),
        "Waypoint": E(missionId="string", lat="float", lon="float", altitudeM="float", seq="integer"),
        "Telemetry": E(droneId="string", lat="float", lon="float", altitudeM="float", recordedAt="datetime"),
        "Payload": E(droneId="string", type="string", weightKg="float"),
        "Swarm": E(name="string", droneCount="integer", leaderId="string"),
    },
    "agent_protocol": {
        "Agent": E(name="string", role="string", modelRef="string", status="string"),
        "Task": E(agentId="string", goal="string", status="string", priority="integer"),
        "Message": E(fromAgentId="string", toAgentId="string", performative="string", content="string"),
        "Tool": E(name="string", description="string", schemaRef="string"),
        "Memory": E(agentId="string", kind="string", contentRef="string"),
        "Plan": E(taskId="string", steps="string", status="string"),
    },
    "qkd": {
        "KeySession": E(aliceNodeId="string", bobNodeId="string", protocol="string", status="string"),
        "Node": E(name="string", location="string", role="string"),
        "Channel": E(sessionId="string", medium="string", lossDb="float"),
        "Key": E(sessionId="string", lengthBits="integer", qber="float", contentRef="string"),
        "Protocol": E(name="string", family="string"),
        "Alarm": E(nodeId="string", type="string", raisedAt="datetime"),
    },
    "fusion_energy": {
        "Shot": E(number="integer", configuration="string", status="string", executedAt="datetime"),
        "Diagnostic": E(shotId="string", instrument="string", channel="string", dataRef="string"),
        "Coil": E(name="string", currentKa="float", status="string"),
        "PlasmaState": E(shotId="string", temperatureKev="float", densityM3="float", betaN="float"),
        "Pulse": E(shotId="string", durationMs="integer", energyMj="float"),
        "Sample": E(shotId="string", parameter="string", value="float", takenAt="datetime"),
    },
}

# ---------------------------------------------------------------------------
# 2. wave-comment -> model-key mapping (parsed from scaffold scripts).
# ---------------------------------------------------------------------------

COMMENT_TO_KEY = {
    # wave2
    "ai/ml": "ai_ml", "martech": "martech", "security/iam": "security_iam",
    "hrtech": "hrtech", "devtools/apm": "devtools_apm",
    "headless/ec/logistics": "headless_ec_logistics", "fintech/web3": "fintech_web3",
    "communications/social": "comms_social", "cx/survey": "cx_survey",
    "vertical saas": "vertical_saas",
    # wave3
    "low-code / ipaas": "lowcode_ipaas", "rpa / process automation": "rpa",
    "modern data stack": "modern_data_stack", "iot / edge": "iot_edge",
    "regtech / privacy": "regtech_privacy", "aec / govtech": "aec_govtech",
    "media / video / cms": "media_video_cms",
    "event mgmt / npo / creator": "event_npo_creator",
    "core banking / insurtech": "core_banking_insurtech",
    "devsecops / api mgmt / serverless": "devsecops_serverless",
    "enterprise commerce / spend mgmt": "enterprise_commerce_spend",
    # wave4 (the comments start with "category N:")
    "india stack & digital public infrastructure (dpg)": "dpg_india_stack",
    "us federal & sovereign infra": "us_federal",
    "uk & europe e-gov": "uk_eu_egov", "japan & apac e-gov": "japan_apac_egov",
    "international organizations & central banks": "intl_orgs_central_banks",
    "open banking & financial regulation": "open_banking_finreg",
    "customs, trade & logistics": "customs_trade_logistics",
    "public health, environment & ip": "public_health_env_ip",
    "public safety, law & justice": "public_safety_law",
    "global public transit & smart cities": "transit_smart_cities",
    # wave5
    "financial market data & trading (hft)": "fin_market_hft",
    "web3 & blockchain rpcs": "web3_rpc",
    "telecom, satellite & connectivity": "telecom_satellite",
    "healthcare hl7/fhir & bioinformatics": "healthcare_fhir_bio",
    "energy, smart grid & utilities": "energy_grid_utilities",
    "deep travel, aviation & hospitality": "travel_aviation_hospitality",
    "open source os & kernel interfaces": "os_kernel",
    "deep ai/ml infrastructure & chips": "ai_ml_infra_chips",
    "cybersecurity threat intel & dark web": "cyber_threat_intel",
    "manufacturing, plm & robotics": "manufacturing_plm_robotics",
    # wave6
    "hardware isas & quantum": "isa_quantum",
    "deep internet & core routing": "internet_routing",
    "mobility, auto & ev": "mobility_auto_ev",
    "space, ocean & earth physics": "space_ocean_earth",
    "agritech, food & precision": "agritech_food",
    "meta-knowledge & scientific publishing": "meta_knowledge_publishing",
    "deep logistics & legacy supply chain": "deep_logistics_supply",
    "materials, bio & chemical": "materials_bio_chemical",
    "energy commodities & trading base": "energy_commodities",
    "ultimate physical benchmarks & classifications": "physical_benchmarks_classifications",
    # wave7 (regional super-apps / fintech)
    "asian super apps & messengers": "comms_social",
    "sea & south asian tech giants": "superapp",
    "latam & african infrastructure": "payments",
    "regional e-commerce & retail": "ecommerce",
    "regional fintech & neo-banks": "payments",
    "local search, delivery & logistics": "delivery_logistics",
    "regional enterprise & saas": "crm_sales",
    "telco mobile money & payment gateways": "payments",
    "ride hailing & micro-mobility": "ride_hailing",
    "digital identity & regional trust": "dpg_india_stack",
    # wave8 (legacy substrate)
    "core payments & switching networks": "payments",
    "mainframes & legacy infrastructure": "mainframe",
    "deep airline & travel legacy": "travel_aviation_hospitality",
    "wholesale banking & custody": "core_banking_insurtech",
    "card networks & acquirers (deep)": "payments",
    "deep telecom billing & routing": "telecom_satellite",
    "heavy industry & scada": "scada",
    "deep shipping & maritime": "deep_logistics_supply",
    "legacy insurance & reinsurance": "core_banking_insurtech",
    "deep retail & pos substrate": "ecommerce",
    # wave9 (deep verticals)
    "deep energy & resource exploration": "energy_commodities",
    "pharmacy benefit managers (pbm) & rx networks": "pharmacy_rx",
    "real estate (mls) & proptech substrate": "real_estate",
    "programmatic adtech & dsp/ssp": "martech",
    "gaming backends & metaverse infra": "gaming_backend",
    "deep legal & ediscovery": "legal_ediscovery",
    "heavy construction & bim": "aec_govtech",
    "specialized insurance underwriting": "core_banking_insurtech",
    "deep aviation & fleet operations": "travel_aviation_hospitality",
    "specialized public sector & defense": "public_safety_law",
    # wave10 (frontier)
    "brain-computer interfaces (bci) & neurotech": "bci_neuro",
    "synthetic biology & dna": "synbio",
    "spatial computing & xr infrastructure": "xr_spatial",
    "autonomous vehicles & v2x": "mobility_auto_ev",
    "drone swarms & aerial robotics": "drone_robotics",
    "ai agent protocols & fipa": "agent_protocol",
    "deep space & off-world infra": "space_ocean_earth",
    "quantum key distribution & cryptography": "qkd",
    "deep deep-sea & subsea data": "space_ocean_earth",
    "fusion, plasma & advanced energy": "fusion_energy",
}

# Wave-1 platform -> model-key (the 100 not covered by wave scripts).
WAVE1_KEYS = {
    "salesforce": "crm_sales", "hubspot": "crm_sales", "pipedrive": "crm_sales",
    "zoho": "crm_sales", "dynamics365": "crm_sales", "servicenow": "vertical_saas",
    "sap": "erp_finance", "oracle": "erp_finance", "netsuite": "erp_finance",
    "workday": "hrtech", "xero": "erp_finance", "billcom": "erp_finance",
    "brex": "payments", "ramp": "payments",
    "aws": "iaas_cloud", "azure": "iaas_cloud", "gcp": "iaas_cloud",
    "digitalocean": "iaas_cloud", "linode": "iaas_cloud", "ovh": "iaas_cloud",
    "heroku": "iaas_cloud", "vercel": "iaas_cloud", "netlify": "iaas_cloud",
    "cloudflare": "iaas_cloud",
    "google-workspace": "office_productivity", "m365": "office_productivity",
    "notion": "office_productivity", "box": "office_productivity",
    "dropbox": "office_productivity", "docusign": "office_productivity",
    "calendly": "office_productivity", "airtable": "office_productivity",
    "monday": "office_productivity", "asana": "office_productivity",
    "trello": "office_productivity", "miro": "office_productivity",
    "github": "devops_ci", "gitlab": "devops_ci", "bitbucket": "devops_ci",
    "atlassian": "devops_ci",
    "jenkins": "devops_ci", "circleci": "devops_ci", "docker": "devops_ci",
    "kubernetes": "devops_ci", "terraform": "devsecops_serverless",
    "postman": "devtools_apm", "datadog": "devtools_apm", "splunk": "devtools_apm",
    "elastic": "devtools_apm",
    "epic-systems": "ehr_health", "cerner": "ehr_health", "meditech": "ehr_health",
    "allscripts": "ehr_health", "athenahealth": "ehr_health",
    "eclinicalworks": "ehr_health", "nextgen": "ehr_health",
    "drchrono": "ehr_health", "curemd": "ehr_health", "greenway": "ehr_health",
    "shopify": "ecommerce", "magento": "ecommerce", "woocommerce": "ecommerce",
    "bigcommerce": "ecommerce", "ecwid": "ecommerce", "wix-stores": "ecommerce",
    "vtex": "ecommerce", "sf-commerce": "ecommerce", "lightspeed": "ecommerce",
    "square-retail": "ecommerce",
    "stripe": "payments", "paypal": "payments", "square": "payments",
    "adyen": "payments", "plaid": "fintech_web3", "coinbase": "fintech_web3",
    "snowflake": "data_analytics", "databricks": "data_analytics",
    "looker": "data_analytics", "tableau": "data_analytics",
    "powerbi": "data_analytics", "mongodb": "data_analytics",
    "redis": "data_analytics", "kafka": "modern_data_stack",
    "figma": "design_tools", "sketch": "design_tools", "invision": "design_tools",
    "canva": "design_tools", "adobe": "design_tools", "blender": "design_tools",
    "rhino": "design_tools", "autodesk": "aec_govtech", "solidworks": "manufacturing_plm_robotics",
    "slack": "comms_social", "zoom": "comms_social", "twilio": "telecom_satellite",
    "sendgrid": "martech", "mailchimp": "martech", "intercom": "cx_survey",
    "zendesk": "cx_survey", "typeform": "cx_survey",
}


def parse_platform_categories():
    """platform -> model-key, from wave scripts + wave1 map."""
    mapping = {}
    for f in sorted(glob.glob(os.path.join(TOOLS_DIR, "scaffold_wave*.py"))):
        txt = open(f).read()
        m = re.search(r"PLATFORMS\s*=\s*\[(.*?)\]", txt, re.S)
        if not m:
            continue
        body = m.group(1)
        current_key = None
        for line in body.splitlines():
            cstart = line.find("#")
            if cstart != -1:
                comment = line[cstart + 1:].strip().lower()
                comment = re.sub(r"^cat(egory)?\s*\d+\s*:\s*", "", comment)
                comment = comment.strip()
                if comment in COMMENT_TO_KEY:
                    current_key = COMMENT_TO_KEY[comment]
            for name in re.findall(r'"([^"]+)"', line):
                if current_key:
                    mapping[name.strip()] = current_key
    # wave1
    for name, key in WAVE1_KEYS.items():
        mapping.setdefault(name, key)
    return mapping


# ---------------------------------------------------------------------------
# 3. Curated overrides — marquee platforms get their real resource models.
#    (Resource set tuned to the public API; falls back to category otherwise.)
# ---------------------------------------------------------------------------

PLATFORM_OVERRIDES = {
    "stripe": {
        "Customer": E(email="string", name="string", phone="string", balance="integer", currency="string"),
        "PaymentIntent": E(customer="string", amount="integer", currency="string", status="string", description="string"),
        "Charge": E(customer="string", paymentIntent="string", amount="integer", currency="string", status="string"),
        "Refund": E(charge="string", amount="integer", reason="string", status="string"),
        "Invoice": E(customer="string", amountDue="integer", currency="string", status="string"),
        "Subscription": E(customer="string", priceId="string", status="string", currentPeriodEnd="datetime"),
        "Product": E(name="string", description="string", active="boolean"),
        "Price": E(product="string", unitAmount="integer", currency="string", recurringInterval="string"),
    },
    "salesforce": {
        "Account": E(name="string", industry="string", annualRevenue="float", ownerId="string", website="string"),
        "Contact": E(accountId="string", firstName="string", lastName="string", email="string", title="string"),
        "Lead": E(company="string", firstName="string", lastName="string", status="string", leadSource="string"),
        "Opportunity": E(accountId="string", name="string", stageName="string", amount="float", closeDate="datetime"),
        "Case": E(accountId="string", subject="string", status="string", priority="string", origin="string"),
        "Campaign": E(name="string", type="string", status="string", budgetedCost="float"),
        "Task": E(whoId="string", subject="string", status="string", activityDate="datetime"),
    },
    "openai": {
        "Model": E(name="string", ownedBy="string", contextWindow="integer"),
        "ChatCompletion": E(modelId="string", prompt="string", output="string", promptTokens="integer", completionTokens="integer"),
        "Embedding": E(modelId="string", input="string", dimensions="integer", vectorRef="string"),
        "FineTuningJob": E(baseModel="string", trainingFile="string", status="string"),
        "File": E(purpose="string", filename="string", bytes="integer"),
        "Assistant": E(name="string", modelId="string", instructions="string"),
        "Thread": E(assistantId="string", status="string"),
    },
    "anthropic": {
        "Model": E(name="string", family="string", contextWindow="integer", maxOutputTokens="integer"),
        "Message": E(modelId="string", role="string", content="string", inputTokens="integer", outputTokens="integer"),
        "Conversation": E(modelId="string", systemPrompt="string", turnCount="integer"),
        "Tool": E(name="string", description="string", inputSchemaRef="string"),
        "ToolUse": E(messageId="string", toolName="string", inputRef="string", status="string"),
        "Batch": E(modelId="string", requestCount="integer", status="string"),
        "File": E(filename="string", mimeType="string", bytes="integer"),
    },
    "twilio": {
        "Message": E(fromNumber="string", toNumber="string", body="string", status="string", direction="string"),
        "Call": E(fromNumber="string", toNumber="string", status="string", durationSec="integer"),
        "PhoneNumber": E(e164="string", capabilities="string", friendlyName="string"),
        "Verification": E(toNumber="string", channel="string", status="string"),
        "Recording": E(callSid="string", durationSec="integer", contentRef="string", status="string"),
        "Conference": E(friendlyName="string", status="string", participantCount="integer"),
    },
    "github": {
        "Repository": E(name="string", owner="string", defaultBranch="string", private="boolean", stars="integer"),
        "Issue": E(repoId="string", number="integer", title="string", state="string", authorId="string"),
        "PullRequest": E(repoId="string", number="integer", title="string", state="string", headRef="string", baseRef="string"),
        "Commit": E(repoId="string", sha="string", message="string", authorId="string"),
        "Workflow": E(repoId="string", name="string", state="string"),
        "WorkflowRun": E(workflowId="string", status="string", conclusion="string", commitSha="string"),
        "Release": E(repoId="string", tag="string", name="string", draft="boolean"),
    },
    "shopify": {
        "Product": E(title="string", vendor="string", productType="string", status="string"),
        "Variant": E(productId="string", sku="string", price="float", inventoryQuantity="integer"),
        "Order": E(customerId="string", number="string", totalPrice="float", currency="string", financialStatus="string"),
        "Customer": E(email="string", firstName="string", lastName="string", ordersCount="integer"),
        "Collection": E(title="string", handle="string", published="boolean"),
        "Fulfillment": E(orderId="string", status="string", trackingNumber="string"),
        "DiscountCode": E(code="string", valueType="string", value="float"),
    },
    "plaid": {
        "Item": E(institutionId="string", status="string", consentExpiresAt="datetime"),
        "Account": E(itemId="string", name="string", type="string", subtype="string", currentBalance="float"),
        "Transaction": E(accountId="string", amount="float", currency="string", category="string", date="datetime"),
        "Institution": E(name="string", country="string", products="string"),
        "Identity": E(accountId="string", ownerName="string", email="string"),
        "Liability": E(accountId="string", type="string", balance="float", apr="float"),
    },
    "slack": {
        "Channel": E(name="string", isPrivate="boolean", topic="string", memberCount="integer"),
        "Message": E(channelId="string", userId="string", text="string", ts="string"),
        "User": E(handle="string", realName="string", email="string", isBot="boolean"),
        "Conversation": E(type="string", creatorId="string"),
        "File": E(name="string", mimeType="string", sizeBytes="integer", uploaderId="string"),
        "Reaction": E(messageTs="string", name="string", count="integer"),
    },
    "aws": {
        "Ec2Instance": E(instanceId="string", instanceType="string", state="string", privateIp="string", region="string"),
        "S3Bucket": E(name="string", region="string", versioning="boolean"),
        "S3Object": E(bucket="string", key="string", sizeBytes="integer", etag="string"),
        "LambdaFunction": E(name="string", runtime="string", memoryMb="integer", timeoutSec="integer"),
        "DynamoTable": E(name="string", partitionKey="string", itemCount="integer", status="string"),
        "IamRole": E(name="string", arn="string", policyRef="string"),
        "RdsInstance": E(identifier="string", engine="string", instanceClass="string", status="string"),
    },
    # Faithful Datadog model (remodeled from the generic devtools_apm archetype),
    # doc-verified to L5 (ADR 260607 §8).
    "datadog": {
        "Monitor": E(name="string", type="string", query="string", message="string", overallState="string", tags="string"),
        "Dashboard": E(title="string", layoutType="string", description="string", widgets="string"),
        "TimeSeries": E(metric="string", type="string", timestamp="integer", value="float", host="string", tags="string"),
        "Event": E(title="string", text="string", timestamp="integer", priority="string", alertType="string", tags="string"),
        "Downtime": E(monitorId="integer", scope="string", start="integer", end="integer", timezone="string"),
        "Incident": E(title="string", severity="string", status="string", customerImpactScope="string"),
    },
    # Faithful SendGrid (Twilio SendGrid) model, doc-verified to L5.
    "sendgrid": {
        "Contact": E(email="string", firstName="string", lastName="string", country="string", externalId="string"),
        "Template": E(name="string", generation="string"),
        "SingleSend": E(name="string", status="string", templateId="string", senderId="string"),
        "Bounce": E(email="string", reason="string", status="string"),
        "UnsubscribeGroup": E(name="string", description="string", isDefault="boolean"),
        "Sender": E(nickname="string", fromEmail="string", fromName="string", verified="boolean"),
    },
    # Faithful GitLab model (remodeled from generic devops_ci), doc-verified L5.
    "gitlab": {
        "Project": E(name="string", path="string", description="string", visibility="string", defaultBranch="string", archived="boolean"),
        "Issue": E(projectId="integer", iid="integer", title="string", description="string", state="string", issueType="string"),
        "MergeRequest": E(projectId="integer", iid="integer", title="string", state="string", sourceBranch="string", targetBranch="string", sha="string"),
        "Pipeline": E(projectId="integer", status="string", ref="string", sha="string", duration="integer"),
        "Job": E(name="string", status="string", stage="string", ref="string"),
        "Commit": E(shortId="string", title="string", message="string", authorName="string", authorEmail="string"),
    },
    # Faithful Mailchimp Marketing model (remodeled from generic martech), L5.
    "mailchimp": {
        "List": E(name="string", permissionReminder="string", useArchiveBar="boolean", notifyOnSubscribe="boolean", notifyOnUnsubscribe="boolean", listRating="integer"),
        "ListMember": E(emailAddress="string", emailType="string", status="string", language="string", vip="boolean", memberRating="integer"),
        "Campaign": E(type="string", contentType="string", status="string", emailTitle="string"),
        "Template": E(name="string", type="string", folderId="string"),
        "Segment": E(name="string", type="string", memberCount="integer"),
        "Automation": E(workflowId="string", type="string", status="string"),
    },
    # Faithful Sentry model (remodeled from generic devtools_apm), doc-verified L5.
    "sentry": {
        "Issue": E(shortId="string", title="string", status="string", level="string", priority="string", count="integer", userCount="integer"),
        "Event": E(eventID="string", groupID="string", projectID="string", title="string", message="string", level="string", platform="string"),
        "Project": E(slug="string", name="string", platform="string", isBookmarked="boolean"),
        "Organization": E(slug="string", name="string", hasAuthProvider="boolean", require2FA="boolean", isEarlyAdopter="boolean"),
        "Team": E(slug="string", name="string", memberCount="integer", hasAccess="boolean"),
        "Release": E(version="string", status="string", commitCount="integer", deployCount="integer"),
    },
    # Faithful Twitch Helix model (remodeled from generic comms_social), L5.
    "twitch": {
        "User": E(userLogin="string", userName="string", broadcasterType="string"),
        "Channel": E(broadcasterLogin="string", broadcasterName="string", broadcasterLanguage="string", gameId="string", gameName="string", title="string", delay="integer"),
        "Stream": E(userId="string", userName="string", gameId="string", gameName="string", type="string", viewerCount="integer", title="string", language="string"),
        "Video": E(userId="string", title="string", description="string", type="string", viewable="string", viewCount="integer", duration="integer"),
        "Clip": E(broadcasterId="string", creatorId="string", gameId="string", title="string", viewCount="integer", duration="float", isFeatured="boolean"),
        "Game": E(name="string", boxArtUrl="string"),
    },
    # Faithful Box model (remodeled from generic office_productivity), L5.
    "box": {
        "File": E(name="string", description="string", size="integer", sha1="string", itemStatus="string", commentCount="integer"),
        "Folder": E(name="string", description="string", size="integer", itemStatus="string", syncState="string"),
        "User": E(name="string", login="string", status="string", role="string"),
        "Collaboration": E(role="string", status="string", isAccessOnly="boolean"),
        "SharedLink": E(access="string", vanityName="string", canDownload="boolean"),
        "Comment": E(message="string", isReplyComment="boolean"),
    },
    # Faithful Figma model (remodeled from generic design_tools), partial L5.
    "figma": {
        "File": E(name="string", role="string", lastModified="datetime", editorType="string", version="string", schemaVersion="integer"),
        "Node": E(id="string", name="string", type="string", visible="boolean", rotation="float", locked="boolean"),
        "Component": E(key="string", name="string", description="string"),
        "Comment": E(fileKey="string", message="string", resolvedAt="datetime"),
        "Project": E(name="string", teamId="string"),
        "Style": E(key="string", name="string", styleType="string"),
    },
    # Faithful Dropbox model (remodeled from generic office_productivity), L5
    # (confirmed against Dropbox's official Stone-generated SDK = the API contract).
    "dropbox": {
        "FileMetadata": E(name="string", pathLower="string", pathDisplay="string", id="string", rev="string", size="integer", isDownloadable="boolean", contentHash="string"),
        "FolderMetadata": E(name="string", pathLower="string", pathDisplay="string", id="string", sharedFolderId="string"),
        "SharedLink": E(url="string", path="string", visibility="string", requestedVisibility="string"),
        "Account": E(accountId="string", email="string", emailVerified="boolean", displayName="string", locale="string", country="string"),
        "SharedFolder": E(sharedFolderId="string", name="string", pathLower="string", accessType="string"),
    },
    # Faithful Cloudflare model (remodeled from generic iaas_cloud), partial L5.
    "cloudflare": {
        "Zone": E(name="string", status="string", type="string", paused="boolean", developmentMode="integer"),
        "DNSRecord": E(name="string", type="string", content="string", ttl="integer", proxied="boolean"),
        "WorkerScript": E(name="string", usageModel="string", createdOn="datetime"),
        "Certificate": E(hosts="string", status="string", type="string"),
        "PageRule": E(targetUrl="string", status="string", priority="integer"),
        "LoadBalancer": E(name="string", enabled="boolean", proxied="boolean"),
    },
    # Faithful Vercel model (remodeled from generic iaas_cloud), L5.
    "vercel": {
        "Deployment": E(name="string", projectId="string", url="string", readyState="string", target="string", type="string"),
        "Project": E(name="string", accountId="string", nodeVersion="string", framework="string", buildCommand="string"),
        "Domain": E(name="string", verified="boolean", serviceType="string", expiresAt="integer"),
        "Alias": E(alias="string", deploymentId="string", projectId="string", redirectStatusCode="integer"),
        "Team": E(name="string", slug="string", description="string"),
    },
    # Faithful Benchling (synthetic-biology R&D cloud) model — doc-verified vs benchling.com/api/v2/openapi.yaml
    "benchling": {
        "CustomEntity": E(apiURL="string", entityRegistryId="string", folderId="string", modifiedAt="datetime", name="string", registryId="string", url="string", webURL="string"),
        "DnaSequence": E(apiURL="string", bases="string", entityRegistryId="string", folderId="string", isCircular="boolean", length="integer", modifiedAt="datetime", name="string", registryId="string", url="string", webURL="string"),
        "Entry": E(apiURL="string", displayId="string", entryTemplateId="string", folderId="string", modifiedAt="string", name="string", webURL="string"),
        "Folder": E(name="string", parentFolderId="string", projectId="string"),
        "Project": E(name="string"),
        "Request": E(apiURL="string", displayId="string", projectId="string", requestStatus="string", scheduledOn="datetime", webURL="string"),
    },
    # Faithful Autodesk Platform Services (APS Data Management) model — doc-verified vs aps.autodesk.com
    "autodesk": {
        "Hub": E(name="string", region="string"),
        "Project": E(name="string"),
        "Folder": E(name="string", displayName="string", createTime="datetime", createUserId="string", createUserName="string", lastModifiedTime="datetime", lastModifiedUserId="string", lastModifiedUserName="string", lastModifiedTimeRollup="datetime", objectCount="integer", hidden="boolean"),
        "Item": E(displayName="string", createTime="datetime", createUserId="string", createUserName="string", lastModifiedTime="datetime", lastModifiedUserId="string", lastModifiedUserName="string", hidden="boolean", reserved="boolean", reservedTime="datetime", reservedUserId="string", reservedUserName="string"),
        "Version": E(name="string", displayName="string", createTime="datetime", createUserId="string", createUserName="string", lastModifiedTime="datetime", lastModifiedUserId="string", lastModifiedUserName="string", versionNumber="integer", storageSize="integer", fileType="string"),
        "Command": E(status="string"),
    },
    # Faithful Universal Robots model (RTDE + Dashboard Server) — doc-verified vs universal-robots.com interface docs
    "universal_robots": {
        "RtdeRobotState": E(timestamp="float", robot_mode="integer", robot_status_bits="integer", safety_mode="integer", safety_status_bits="integer", actual_main_voltage="float", actual_robot_voltage="float", actual_robot_current="float"),
        "RtdeExecutionState": E(runtime_state="integer", actual_execution_time="float", speed_scaling="float", target_speed_fraction="float"),
        "RtdeToolState": E(tool_mode="integer", tool_output_voltage="integer", tool_output_current="float", tool_temperature="float"),
        "DashboardRobotState": E(robotmode="string", safetystatus="string", running="boolean"),
        "DashboardProgram": E(programName="string", state="string"),
        "DashboardInstallation": E(installationName="string"),
    },
    # Faithful Materials Project model — doc-verified vs api.materialsproject.org/openapi.json
    "materials_project": {
        "SummaryDoc": E(material_id="string", formula_pretty="string", formula_anonymous="string", chemsys="string", volume="float", density="float", density_atomic="float", nsites="integer", nelements="integer", theoretical="boolean", deprecated="boolean", is_stable="boolean", is_magnetic="boolean", is_metal="boolean", is_gap_direct="boolean", band_gap="float", efermi="float", formation_energy_per_atom="float", energy_above_hull="float", uncorrected_energy_per_atom="float", energy_per_atom="float", equilibrium_reaction_energy_per_atom="float", total_magnetization="float", total_magnetization_normalized_vol="float"),
        "MaterialsDoc": E(material_id="string", formula_pretty="string", formula_anonymous="string", chemsys="string", volume="float", density="float", density_atomic="float", nsites="integer", nelements="integer", last_updated="datetime"),
        "ThermoDoc": E(material_id="string", thermo_type="string", energy_type="string", uncorrected_energy_per_atom="float", energy_per_atom="float", formation_energy_per_atom="float", energy_above_hull="float", is_stable="boolean", equilibrium_reaction_energy_per_atom="float", decomposition_enthalpy="float"),
        "CoreTaskDoc": E(task_id="string", task_type="string", run_type="string", calc_type="string", batch_id="string", dir_name="string", vasp_version="string", completed_at="datetime", last_updated="datetime", nsites="integer"),
        "ElectronicStructureDoc": E(material_id="string", band_gap="float", cbm="float", vbm="float", efermi="float", is_gap_direct="boolean", is_metal="boolean", magnetic_ordering="string"),
        "MagnetismDoc": E(material_id="string", ordering="string", is_magnetic="boolean", total_magnetization="float", total_magnetization_normalized_vol="float", total_magnetization_normalized_formula_units="float", num_magnetic_sites="integer", num_unique_magnetic_sites="integer", exchange_symmetry="integer"),
    },
    # Faithful athenahealth (cloud EHR) model — doc-verified vs docs.athenahealth.com/api (API-shape only, no PHI)
    "athenahealth": {
        "Patient": E(homeboundyn="boolean", assignedsexatbirth="string", altfirstname="string", ethnicitycode="string", industrycode="integer", language6392code="string", localpatientid="string", deceaseddate="string", firstappointment="string", primaryproviderid="integer", genderidentityother="string", preferredpronouns="string", lastappointment="string", donotcallyn="boolean", primarydepartmentid="integer", status="string", lastemail="string", racecode="string", sexualorientation="string", genderidentity="string", emailexistsyn="boolean", occupationcode="integer", sexualorientationother="string", patientid="integer"),
        "Appointment": E(reasonid="integer", appointmentstatus="string", cancelleddatetime="string", chargeentrynotrequired="boolean", hl7providerid="integer", cancelreasonname="string", chargeentrynotrequiredreason="string", lastmodified="string", departmentid="integer", checkoutdatetime="string", copay="string", encounterid="string", scheduledby="string", checkindatetime="string", cancelledby="string", stopintakedatetime="string", encounterstatus="string", frozenyn="boolean", appointmenttype="string", appointmenttypeid="integer", cancelreasonid="integer", cancelreasonnoshow="boolean", cancelreasonslotavailable="boolean", coordinatorenterpriseyn="boolean"),
        "Encounter": E(encounterid="integer", appointmentid="integer", departmentid="integer", encountervisitname="string", encountertype="string", status="string", patientlocationid="integer", patientlocation="string", patientstatusid="integer", patientstatus="string", encounterdate="string", stage="string", providerid="integer", providerfirstname="string", providerlastname="string", providerphone="string", lastupdated="string"),
        "Claim": E(referringproviderid="integer", claimcreateddate="string", billedservicedate="string", billedproviderid="integer", appointmentid="integer", chargeamount="string", transactionid="integer", claimid="integer"),
        "Provider": E(billable="boolean", ansispecialtycode="string", firstname="string", entitytype="string", otherprovideridlist="string", ansinamecode="string", displayname="string", homedepartment="string", providerid="integer", providertypeid="string", providerusername="string", supervisingproviderid="integer", providertype="string", createencounterprovideridlist="string", schedulingname="string", usualdepartmentid="string", createencounteroncheckinyn="boolean", specialty="string", hideinportalyn="boolean", lastname="string", npi="integer", providergrouplist="string", federalidnumber="string", supervisingproviderusername="string"),
        "Department": E(timezoneoffset="integer", singleappointmentcontractmax="string", state="string", placeofservicefacility="boolean", latitude="string", departmentid="integer", address="string", placeofservicetypeid="string", longitude="string", clinicals="string", timezone="integer", name="string", patientdepartmentname="string", chartsharinggroupid="string", placeofservicetypename="string", zip="string", timezonename="string", communicatorbrandid="string", medicationhistoryconsent="boolean", ishospitaldepartment="boolean", providergroupid="string", portalurl="string", city="string", servicedepartment="boolean"),
    },
    # Faithful Epic on FHIR R4 model — doc-verified vs fhir.epic.com (API-shape only, no PHI)
    "epic-systems": {
        "Patient": E(resourceType="string", implicitRules="string", language="string", active="boolean", gender="string", birthDate="string", deceasedBoolean="boolean", deceasedDateTime="string", multipleBirthBoolean="boolean", multipleBirthInteger="integer"),
        "Observation": E(resourceType="string", implicitRules="string", language="string", status="string", issued="string"),
        "Encounter": E(resourceType="string", implicitRules="string", language="string", status="string"),
        "Condition": E(resourceType="string", implicitRules="string", language="string", recordedDate="string"),
        "MedicationRequest": E(resourceType="string", implicitRules="string", language="string", status="string", intent="string", priority="string", doNotPerform="boolean", reportedBoolean="boolean", authoredOn="string", instantiatesUri="string"),
        "Procedure": E(resourceType="string", implicitRules="string", language="string", instantiatesUri="string", status="string"),
    },
    # Faithful Oracle Health/Cerner Millennium FHIR R4 model — doc-verified vs fhir.cerner.com/millennium/r4 (API-shape only, no PHI)
    "cerner": {
        "Patient": E(active="boolean", gender="string", birthDate="datetime", deceasedBoolean="boolean", deceasedDateTime="datetime", multipleBirthBoolean="boolean", multipleBirthInteger="integer"),
        "Observation": E(status="string", effectiveDateTime="datetime", effectiveInstant="datetime", issued="datetime", valueString="string", valueBoolean="boolean", valueInteger="integer", valueDateTime="datetime"),
        "Encounter": E(status="string"),
        "Condition": E(recordedDate="datetime", onsetDateTime="datetime", abatementDateTime="datetime"),
        "MedicationRequest": E(status="string", intent="string", priority="string", doNotPerform="boolean", reportedBoolean="boolean", authoredOn="datetime"),
        "AllergyIntolerance": E(type="string", criticality="string", recordedDate="datetime", onsetDateTime="datetime", lastOccurrence="datetime"),
    },
    # Faithful Bentley iTwin Platform model — doc-verified vs developer.bentley.com/apis
    "bentley": {
        "iModel": E(name="string", description="string", iTwinId="string", state="string", createdDateTime="datetime", dataCenterLocation="string", initialized="boolean", displayName="string"),
        "iTwin": E(subClass="string", type="string", status="string", displayName="string", number="string", iTwinAccountId="string"),
        "Changeset": E(index="integer", displayName="string", description="string", parentId="string", pushDateTime="datetime", creatorId="string", briefcaseId="integer", changesetGroupId="string", fileSize="integer", state="string"),
        "NamedVersion": E(displayName="string", changesetId="string", changesetIndex="integer", name="string", description="string", createdDateTime="datetime", state="string"),
        "Connection": E(displayName="string", description="string", iModelId="string", iTwinId="string", connectorName="string", authenticationType="string"),
        "Job": E(status="string", progress="integer", createdDateTime="datetime", lastModifiedDateTime="datetime", iModelId="string", iTwinId="string", testId="string", changesetId="string"),
    },
    # Faithful Miro (REST API v2) model (remodeled from the generic
    # office_productivity archetype whose Workspace/Document/Folder doc entities
    # did not match Miro's whiteboard API), doc-verified L5 vs
    # github.com/miroapp/api-clients (generated miro-api model TS).
    "miro": {
        "Board": E(name="string", description="string", type="string", viewLink="string"),
        "Item": E(type="string"),
        "Tag": E(title="string", fillColor="string", type="string"),
        "BoardMember": E(name="string", role="string", type="string"),
        "Organization": E(name="string", plan="string", fullLicensesPurchased="integer", type="string"),
        "Connector": E(shape="string", isSupported="boolean", type="string"),
    },

    # Faithful X (Twitter API v2) model (remodeled from the generic comms_social
    # chat archetype whose Channel/Message/Room entities did not match X's
    # microblog API), doc-verified L5 vs the official api.twitter.com/2/openapi.json.
    "x": {
        "Tweet": E(text="string", lang="string", source="string", paidPartnership="boolean", possiblySensitive="boolean", replySettings="string", conversationId="string", authorId="string"),
        "User": E(name="string", description="string", location="string", url="string", protected="boolean", verified="boolean", verifiedType="string", subscriptionType="string", profileImageUrl="string", profileBannerUrl="string", receivesYourDm="boolean"),
        "Space": E(title="string", state="string", lang="string", isTicketed="boolean", participantCount="integer", subscriberCount="integer", scheduledStart="datetime", startedAt="datetime", endedAt="datetime"),
        "List": E(name="string", description="string", private="boolean", followerCount="integer", memberCount="integer"),
        "Media": E(type="string"),
        "Poll": E(durationMinutes="integer", endDatetime="datetime", votingStatus="string"),
    },

    # Faithful Paystack model (remodeled from the generic Stripe-shaped payments
    # archetype whose Customer/PaymentIntent/Charge/Payout entities did not match
    # Paystack's API), doc-verified L5 vs github.com/PaystackOSS/openapi.
    "paystack": {
        "Transaction": E(email="string", amount="integer", reference="string", callbackUrl="string", plan="string", invoiceLimit="integer", splitCode="string", subaccount="string", transactionCharge="string", bearer="string", label="string"),
        "Customer": E(email="string", firstName="string", lastName="string", phone="string", metadata="string"),
        "Plan": E(name="string", amount="integer", interval="string", description="string", sendInvoices="boolean", sendSms="boolean", currency="string", invoiceLimit="integer"),
        "Subscription": E(customer="string", plan="string", authorization="string", startDate="datetime"),
        "Product": E(name="string", description="string", price="integer", currency="string", unlimited="boolean", quantity="integer", splitCode="string", metadata="string"),
        "Page": E(name="string", description="string", amount="integer", currency="string", slug="string", type="string", plan="string", fixedAmount="boolean", splitCode="string", redirectUrl="string", successMessage="string", notificationEmail="string", collectPhone="boolean"),
    },

    # Faithful Vimeo model (remodeled from the generic media_video_cms archetype
    # whose Asset/Rendition/Channel/Playlist entities did not match Vimeo's video
    # API), doc-verified L5 vs Vimeo's official OpenAPI (via apis.guru).
    "vimeo": {
        "Video": E(name="string", description="string", duration="float", width="integer", height="integer", language="string", license="string", status="string", link="string", releaseTime="datetime", resourceKey="string", uri="string"),
        "Channel": E(name="string", description="string", link="string", resourceKey="string", uri="string"),
        "Album": E(name="string", description="string", duration="float", layout="string", sort="string", theme="string", brandColor="string", allowDownloads="boolean", allowShare="boolean", allowContinuousPlay="boolean", reviewMode="boolean", hideNav="boolean", link="string", url="string", resourceKey="string", uri="string"),
        "User": E(name="string", bio="string", email="string", location="string", account="string", link="string", resourceKey="string", uri="string"),
        "Group": E(name="string", description="string", link="string", resourceKey="string", uri="string"),
        "Category": E(name="string", topLevel="boolean", lastVideoFeaturedTime="datetime", link="string", resourceKey="string", uri="string"),
    },

    # Faithful DrChrono (EHR) model (remodeled from the generic FHIR-shaped health
    # archetype — Encounter/Observation/Practitioner — to DrChrono's proprietary
    # REST entities), doc-verified L5 vs DrChrono's official OpenAPI (via apis.guru).
    # API-shape only (field names/types); no real PHI is stored.
    "drchrono": {
        "Patient": E(chartId="string", dateOfBirth="string", email="string", cellPhone="string", address="string", city="string", copay="string", defaultPharmacy="string", disableSmsMessages="boolean", doctor="integer", emergencyContactName="string", emergencyContactPhone="string", employer="string", dateOfFirstAppointment="string", dateOfLastAppointment="string"),
        "Appointment": E(doctor="integer", duration="integer", examRoom="integer", color="string", billingStatus="string", ins1Status="string", allowOverlapping="boolean", apptIsBreak="boolean", deletedFlag="boolean", baseRecurringAppointment="string", billingProvider="string", firstBilledDate="string"),
        "Doctor": E(firstName="string", lastName="string", email="string", cellPhone="string", officePhone="string", npiNumber="string", groupNpiNumber="string", specialty="string", jobTitle="string", practiceGroupName="string", isAccountSuspended="boolean"),
        "Office": E(name="string", address="string", city="string", state="string", zipCode="string", phoneNumber="string", faxNumber="string", doctor="string", archived="boolean", onlineScheduling="boolean", startTime="string", endTime="string", taxIdNumberProfessional="string"),
        "ClinicalNote": E(patient="string", appointment="string", archived="boolean"),
        "LabResult": E(labTest="integer", labOrder="string", observationCode="string", observationDescription="string", value="string", unit="string", normalRange="string", abnormalStatus="string", status="string", comments="string", groupCode="string", testPerformed="string", specimenReceived="string"),
    },
    # Faithful Airtable model (remodeled from generic office_productivity), L5.
    "airtable": {
        "Base": E(name="string", permissionLevel="string"),
        "Table": E(name="string", description="string", primaryFieldId="string"),
        "Field": E(name="string", type="string", description="string"),
        "Record": E(createdTime="datetime", fieldsJson="string"),
        "View": E(name="string", type="string", personalForUserId="string"),
        "Comment": E(text="string", lastUpdatedTime="datetime"),
    },
    # Faithful Greenhouse Harvest model (remodeled from generic hrtech), L5.
    "greenhouse": {
        "Candidate": E(firstName="string", lastName="string", email="string", canEmail="boolean"),
        "Application": E(candidateId="string", prospect="boolean", appliedAt="datetime", status="string", jobPostId="string"),
        "Job": E(name="string", requisitionId="string", status="string"),
        "Offer": E(applicationId="string", candidateId="string", jobId="string", status="string", startDate="datetime"),
        "Scorecard": E(applicationId="string", interviewerId="string", score="string", notes="string"),
        "ScheduledInterview": E(applicationId="string", name="string", scheduledAt="datetime", videoConferencingUrl="string"),
    },
    # Faithful Pipedrive model (remodeled from generic crm_sales), L5.
    "pipedrive": {
        "Deal": E(title="string", value="float", currency="string", status="string", probability="float", pipelineId="integer", stageId="integer"),
        "Person": E(name="string", ownerId="integer", orgId="integer", marketingStatus="string"),
        "Organization": E(name="string", ownerId="integer"),
        "Pipeline": E(name="string", isDealProbabilityEnabled="boolean"),
        "Stage": E(name="string", pipelineId="integer", dealProbability="integer"),
        "Activity": E(subject="string", type="string", done="boolean", dueDate="string"),
    },
    # Faithful Klaviyo model (remodeled from generic martech), L5.
    "klaviyo": {
        "Profile": E(email="string", phoneNumber="string", externalId="string"),
        "List": E(name="string"),
        "Segment": E(name="string", isActive="boolean", isStarred="boolean"),
        "Campaign": E(name="string", status="string", archived="boolean"),
        "Flow": E(name="string", status="string", triggerType="string", archived="boolean"),
        "Event": E(metricId="string", profileId="string", timestamp="integer"),
    },
    # Faithful Databricks model (remodeled from generic data_analytics), L5
    # (confirmed against the official databricks-sdk-py source).
    "databricks": {
        "Cluster": E(clusterName="string", state="string", sparkVersion="string", numWorkers="integer"),
        "Job": E(jobId="integer", creatorUserName="string", createdTime="datetime"),
        "Run": E(runId="integer", jobId="integer", state="string", runName="string", startTime="datetime"),
        "Warehouse": E(name="string", state="string", warehouseType="string", clusterSize="string"),
        "ObjectInfo": E(path="string", objectType="string", language="string", size="integer"),
    },
    # Faithful Xero Accounting model (remodeled from generic erp_finance), L5
    # (confirmed against the official XeroAPI/xero-node SDK models).
    "xero": {
        "Invoice": E(invoiceNumber="string", type="string", status="string", total="float", amountDue="float"),
        "Contact": E(name="string", emailAddress="string", contactStatus="string", taxNumber="string", isSupplier="boolean", isCustomer="boolean"),
        "Account": E(code="string", name="string", type="string", status="string", bankAccountNumber="string"),
        "Payment": E(amount="float", status="string", paymentType="string", isReconciled="boolean"),
        "BankTransaction": E(type="string", status="string", total="float", reference="string", isReconciled="boolean"),
        "CreditNote": E(creditNoteNumber="string", type="string", status="string", total="float"),
    },
    # Faithful Notion model (remodeled from generic office_productivity), L5
    # (confirmed against the official makenotion/notion-sdk-js types).
    "notion": {
        "Page": E(object="string", createdTime="datetime", lastEditedTime="datetime", inTrash="boolean", url="string"),
        "Database": E(object="string", title="string", description="string", isInline="boolean", url="string"),
        "Block": E(object="string", type="string", hasChildren="boolean"),
        "User": E(object="string", name="string", type="string", avatarUrl="string"),
        "Comment": E(discussionId="string", createdTime="datetime"),
    },
    # Faithful Zoom model (remodeled from generic comms_social), partial L5.
    "zoom": {
        "Meeting": E(topic="string", type="integer", status="string", duration="integer", timezone="string", hostId="string", startTime="datetime"),
        "Webinar": E(topic="string", type="integer", duration="integer", hostId="string"),
        "Recording": E(meetingId="string", recordingType="string", duration="integer", fileSize="integer", status="string"),
        "Registrant": E(email="string", firstName="string", lastName="string", status="string"),
        "User": E(email="string", firstName="string", lastName="string", type="integer", status="string"),
    },
    # Faithful Asana model (recovered from the official Asana OpenAPI spec), L5.
    "asana": {
        "Task": E(name="string", resourceSubtype="string", completed="boolean", completedAt="datetime", createdAt="datetime", approvalStatus="string", dueAt="datetime"),
        "Project": E(name="string", archived="boolean", color="string", completed="boolean", defaultView="string"),
        "Section": E(name="string", createdAt="datetime"),
        "User": E(name="string", email="string"),
        "Tag": E(name="string", color="string", notes="string"),
        "Workspace": E(name="string", isOrganization="boolean"),
    },
    # Faithful Coinbase Advanced Trade model (recovered from coinbase-advanced-py
    # SDK), L5. Numeric values are strings per the SDK contract.
    "coinbase": {
        "Order": E(orderId="string", productId="string", side="string", status="string", clientOrderId="string", orderType="string"),
        "Fill": E(entryId="string", tradeId="string", orderId="string", price="string", size="string", productId="string", side="string"),
        "Account": E(uuid="string", name="string", currency="string", default="boolean", active="boolean", type="string"),
        "Product": E(productId="string", price="string", volume24h="string", productType="string", status="string"),
        "Portfolio": E(uuid="string", name="string", type="string"),
        "PortfolioPosition": E(asset="string", totalBalanceFiat="float", totalBalanceCrypto="float", allocation="float"),
    },
    # Faithful HubSpot CRM model (recovered from the official public OpenAPI
    # spec). Contact + Pipeline doc-confirmed; the other objects use HubSpot's
    # generic property system (standard props, not confirmed this fetch).
    "hubspot": {
        "Contact": E(email="string", firstname="string", lastname="string", company="string", phone="string", website="string"),
        "Company": E(name="string", domain="string", industry="string"),
        "Deal": E(dealname="string", dealstage="string", amount="float", pipeline="string"),
        "Ticket": E(subject="string", hsTicketPriority="string", hsPipelineStage="string"),
        "LineItem": E(name="string", quantity="integer", price="float"),
        "Pipeline": E(label="string", displayOrder="integer"),
    },
    # Faithful Jira Cloud model (recovered from the official Atlassian swagger), L5.
    "atlassian": {
        "Project": E(key="string", name="string", projectTypeKey="string", style="string", archived="boolean", simplified="boolean"),
        "IssueType": E(name="string", description="string", subtask="boolean", hierarchyLevel="integer"),
        "Status": E(name="string", description="string"),
        "StatusCategory": E(key="string", name="string", colorName="string"),
        "User": E(accountId="string", accountType="string", displayName="string", emailAddress="string", active="boolean"),
        "Comment": E(body="string", created="datetime", updated="datetime", jsdPublic="boolean"),
    },
    # Faithful DocuSign eSignature model (recovered from the official OpenAPI v2.1), L5.
    "docusign": {
        "Envelope": E(emailSubject="string", status="string", sentDateTime="datetime", completedDateTime="datetime", envelopeId="string"),
        "Signer": E(email="string", firstName="string", lastName="string", status="string", signedDateTime="datetime"),
        "Document": E(documentId="string", name="string", order="integer"),
        "SignHereTab": E(tabId="string", pageNumber="string", xPosition="string", yPosition="string"),
        "EnvelopeTemplate": E(templateId="string", name="string", status="string", description="string"),
    },
    # Faithful Gusto model (recovered from the official Gusto Python SDK), L5.
    "gusto": {
        "Employee": E(uuid="string", firstName="string", lastName="string", email="string", onboardingStatus="string", paymentMethod="string", terminated="boolean", flsaStatus="string"),
        "Company": E(uuid="string", name="string", status="string", entityType="string", tier="string"),
        "Compensation": E(rate="string", paymentUnit="string", flsaStatus="string", effectiveDate="string", adjustForMinimumWage="boolean"),
        "Job": E(uuid="string", title="string", rate="string", paymentUnit="string", primary="boolean"),
        "Contractor": E(firstName="string", lastName="string", businessName="string", wageType="string", contractorType="string", isActive="boolean"),
        "Payroll": E(uuid="string", processed="boolean", offCycle="boolean", offCycleReason="string"),
    },
    # Faithful MongoDB Atlas model (remodeled from generic data_analytics), L5
    # (confirmed against the official mongodb/openapi Atlas Admin API v2 spec).
    "mongodb": {
        "Cluster": E(name="string", clusterType="string", stateName="string", mongoDBVersion="string"),
        "DatabaseUser": E(username="string", databaseName="string", awsIAMType="string"),
        "Project": E(name="string", orgId="string", clusterCount="integer"),
        "Backup": E(frequencyType="string", description="string"),
        "Organization": E(orgName="string", planType="string", groupId="string"),
        "NetworkPeering": E(name="string", accepterAccountId="string", localStatus="string", cloudStatus="string"),
    },
    # Faithful Intercom model (remodeled from generic cx_survey), L5
    # (confirmed against the official Intercom OpenAPI v2.15). *_at are unix int.
    "intercom": {
        "Contact": E(email="string", phone="string", name="string", role="string", createdAt="integer", signedUpAt="integer"),
        "Conversation": E(state="string", priority="string", open="boolean", read="boolean", adminAssigneeId="integer"),
        "Company": E(name="string", industry="string", monthlySpend="integer", size="integer", companyId="string"),
        "Admin": E(name="string", email="string", awayModeEnabled="boolean", hasInboxSeat="boolean", jobTitle="string"),
        "Article": E(title="string", body="string", state="string", authorId="integer"),
        "Tag": E(name="string", appliedAt="integer"),
    },
    # Faithful monday.com model (remodeled from generic office_productivity), L5
    # (confirmed against the official monday-graphql-api SDK types).
    "monday": {
        "Board": E(name="string", description="string", state="string", boardKind="string", itemsCount="integer"),
        "Item": E(name="string", email="string", creatorId="string", state="string"),
        "Column": E(title="string", description="string", type="string", archived="boolean", width="integer"),
        "Group": E(title="string", color="string", position="string", archived="boolean"),
        "User": E(name="string", email="string", enabled="boolean", isAdmin="boolean", isGuest="boolean", countryCode="string"),
        "Update": E(body="string", textBody="string", creatorId="string", itemId="string"),
    },
    # Faithful PayPal model (remodeled from generic payments), L5
    # (confirmed against the official paypal-rest-api-specifications OpenAPI).
    "paypal": {
        "Order": E(status="string", intent="string"),
        "Authorization": E(status="string", createTime="datetime", updateTime="datetime"),
        "Capture": E(status="string", invoiceId="string", customId="string"),
        "Refund": E(status="string", invoiceId="string", customId="string"),
        "Plan": E(productId="string", status="string", name="string", description="string"),
        "Subscription": E(status="string", planId="string", createTime="datetime", startTime="datetime"),
    },
    # Faithful Adyen Checkout model (remodeled from generic payments), L5
    # (confirmed against the official Adyen CheckoutService v71 OpenAPI).
    "adyen": {
        "PaymentRequest": E(reference="string", merchantAccount="string", shopperEmail="string", channel="string", recurringProcessingModel="string", storePaymentMethod="boolean"),
        "PaymentResponse": E(pspReference="string", resultCode="string", merchantReference="string", refusalReason="string", refusalReasonCode="string"),
        "Amount": E(currency="string", value="integer"),
        "PaymentRefundRequest": E(merchantAccount="string", reference="string", merchantRefundReason="string"),
        "PaymentRefundResponse": E(pspReference="string", paymentPspReference="string", status="string", merchantRefundReason="string", reference="string"),
        "PaymentCaptureResponse": E(pspReference="string", paymentPspReference="string", status="string", merchantAccount="string", reference="string"),
    },
    # Faithful Looker API 4.0 model (remodeled from generic data_analytics), L5
    # (confirmed against the official looker-open-source/sdk-codegen spec).
    "looker": {
        "Look": E(title="string", public="boolean", queryId="string", userId="string", deleted="boolean"),
        "Dashboard": E(title="string", folderId="string", userId="string", viewCount="integer"),
        "Query": E(model="string", view="string", slug="string", queryTimezone="string", hasTableCalculations="boolean"),
        "User": E(email="string", firstName="string", lastName="string", isDisabled="boolean"),
        "Folder": E(name="string", parentId="string", creatorId="string"),
        "ScheduledPlan": E(name="string", userId="string", enabled="boolean"),
    },
    # Faithful Snowflake model (remodeled from generic data_analytics), L5
    # (confirmed against the official snowflakedb/snowflake-rest-api-specs).
    "snowflake": {
        "Warehouse": E(name="string", warehouseType="string", warehouseSize="string", scalingPolicy="string", autoSuspend="integer", autoResume="boolean", state="string"),
        "Database": E(name="string", kind="string", owner="string", retentionTime="integer", isDefault="boolean"),
        "Schema": E(name="string", kind="string", databaseName="string", owner="string", managedAccess="boolean"),
        "Table": E(name="string", kind="string", databaseName="string", schemaName="string", rows="integer"),
        "Task": E(name="string", warehouse="string", state="string", owner="string"),
        "Role": E(name="string", owner="string", comment="string"),
    },
    # Faithful Power BI model (recovered via official Microsoft Learn REST docs), L5.
    "powerbi": {
        "Dataset": E(name="string", description="string", contentProviderType="string", targetStorageMode="string", isRefreshable="boolean", addRowsAPIEnabled="boolean"),
        "Report": E(name="string", description="string", reportType="string", datasetId="string", isOwnedByMe="boolean"),
        "Dashboard": E(displayName="string", isReadOnly="boolean"),
        "Group": E(name="string", isReadOnly="boolean", isOnDedicatedCapacity="boolean", defaultDatasetStorageFormat="string"),
        "Tile": E(title="string", reportId="string", datasetId="string", rowSpan="integer", colSpan="integer"),
        "Gateway": E(name="string", type="string", gatewayStatus="string"),
    },
    # Faithful Alpaca Trading model (recovered via alpaca-py SDK), L5. Numeric=string.
    "alpaca": {
        "Asset": E(symbol="string", assetClass="string", exchange="string", status="string", tradable="boolean", fractionable="boolean"),
        "Order": E(symbol="string", side="string", type="string", status="string", qty="string", timeInForce="string"),
        "Position": E(symbol="string", qty="string", side="string", avgEntryPrice="string", marketValue="string"),
        "TradeAccount": E(accountNumber="string", status="string", equity="string", cash="string", buyingPower="string", patternDayTrader="boolean"),
        "TradeActivity": E(symbol="string", side="string", price="float", qty="float", type="string", orderId="string"),
    },
    # Faithful Vonage model (recovered via official Vonage API docs), L5.
    "vonage": {
        "Call": E(fromNumber="string", toNumber="string", status="string", direction="string", duration="integer", price="float"),
        "Message": E(messageId="string", toNumber="string", fromNumber="string", status="string", messageType="string", channel="string"),
        "Number": E(msisdn="string", country="string", type="string", cost="float"),
        "Verification": E(requestId="string", number="string", status="string", codeLength="integer"),
        "Application": E(name="string", type="string", answerUrl="string"),
    },
    # Faithful Segment model — verified against segmentio/facade (the open-source
    # event parser all SDKs share); the `type` discriminator is a documented closed set.
    "segment": {
        "TrackEvent": E(type="string", event="string", userId="string", anonymousId="string", messageId="string", timestamp="datetime"),
        "IdentifyEvent": E(type="string", userId="string", anonymousId="string", messageId="string", timestamp="datetime"),
        "PageEvent": E(type="string", userId="string", anonymousId="string", category="string", name="string", messageId="string", timestamp="datetime"),
        "GroupEvent": E(type="string", userId="string", anonymousId="string", groupId="string", messageId="string", timestamp="datetime"),
        "Source": E(name="string", slug="string", enabled="boolean", workspaceId="string"),
        "Destination": E(name="string", enabled="boolean", sourceId="string", workspaceId="string"),
    },
    # Faithful Marqeta Core API model — verified against the official Marqeta
    # OpenAPI 3.0.40 spec (github.com/marqeta/marqeta-openapi).
    "marqeta": {
        "Card": E(token="string", state="string", lastFour="string", cardProductToken="string", userToken="string", fulfillmentStatus="string", createdTime="datetime"),
        "CardProduct": E(token="string", name="string", active="boolean", createdTime="datetime"),
        "User": E(token="string", firstName="string", lastName="string", email="string", status="string", active="boolean", createdTime="datetime"),
        "Transaction": E(token="string", amount="float", type="string", state="string", cardToken="string", userToken="string", createdTime="datetime"),
        "FundingSource": E(token="string", type="string", active="boolean", isDefaultAccount="boolean", createdTime="datetime"),
    },
    # Faithful Plaid model — verified against the official Plaid OpenAPI
    # (github.com/plaid/plaid-openapi 2020-09-14.yml). Object/array fields dropped.
    "plaid": {
        "Account": E(accountId="string", name="string", officialName="string", mask="string", type="string", subtype="string", verificationStatus="string"),
        "AccountBalance": E(available="float", current="float", limit="float", isoCurrencyCode="string", lastUpdatedDatetime="datetime"),
        "Transaction": E(accountId="string", transactionId="string", amount="float", date="datetime", pending="boolean", name="string", merchantName="string", isoCurrencyCode="string", paymentChannel="string", checkNumber="string"),
        "Item": E(itemId="string", institutionId="string", institutionName="string", webhook="string", authMethod="string", oauth="boolean"),
        "Institution": E(institutionId="string", name="string", url="string", oauth="boolean"),
        "Holding": E(accountId="string", securityId="string", symbol="string", name="string", quantity="float", institutionValue="float", costBasis="float", currencyCode="string"),
    },
    # Faithful Adyen model — verified against the official Adyen OpenAPI
    # (github.com/Adyen/adyen-openapi). PARTIAL: resultCode closed sets enforced;
    # eventCode flagged non-exhaustive by source -> left as gap. Object refs dropped.
    "adyen": {
        "Payment": E(pspReference="string", merchantReference="string", merchantAccount="string", reference="string", resultCode="string", shopperReference="string"),
        "Amount": E(value="integer", currency="string"),
        "ModificationResult": E(pspReference="string", resultCode="string", response="string"),
        "PaymentMethod": E(type="string", storedPaymentMethodId="string"),
        "Notification": E(eventCode="string", pspReference="string", merchantReference="string", eventDate="datetime", success="boolean"),
    },
    # Faithful PagerDuty model — verified against the official PagerDuty OpenAPI
    # 3.0.2 (github.com/PagerDuty/api-schema). snake_case -> camelCase.
    "pagerduty": {
        "Incident": E(title="string", incidentNumber="integer", status="string", urgency="string", incidentKey="string", assignedVia="string", createdAt="datetime", updatedAt="datetime", resolvedAt="datetime"),
        "Service": E(name="string", description="string", status="string", autoResolveTimeout="integer", acknowledgementTimeout="integer", createdAt="datetime"),
        "EscalationPolicy": E(name="string", description="string", numLoops="integer", onCallHandoffNotifications="string"),
        "User": E(name="string", email="string", role="string", timeZone="string", jobTitle="string", invitationSent="boolean"),
        "Schedule": E(name="string", description="string", timeZone="string"),
        "Team": E(name="string", description="string", defaultRole="string"),
    },
    # Faithful DigitalOcean model — verified against the official DigitalOcean
    # OpenAPI (github.com/digitalocean/openapi). Array fields dropped.
    "digitalocean": {
        "Droplet": E(id="integer", name="string", status="string", memory="integer", vcpus="integer", disk="integer", locked="boolean", createdAt="datetime"),
        "Volume": E(id="string", name="string", sizeGigabytes="integer", filesystemType="string", createdAt="datetime"),
        "DatabaseCluster": E(id="string", name="string", engine="string", numNodes="integer", size="string", region="string", status="string", createdAt="datetime"),
        "LoadBalancer": E(id="string", name="string", ip="string", status="string", sizeUnit="integer", createdAt="datetime"),
        "KubernetesCluster": E(id="string", name="string", region="string", version="string", endpoint="string", autoUpgrade="boolean", ha="boolean", createdAt="datetime"),
        "Image": E(id="integer", name="string", slug="string", public="boolean", status="string", type="string", sizeGigabytes="float", createdAt="datetime"),
    },
    # Faithful Razorpay model — verified against the official razorpay-python SDK
    # (github.com/razorpay/razorpay-python). amounts in paise (integer); timestamps epoch.
    "razorpay": {
        "Payment": E(id="string", amount="integer", currency="string", status="string", method="string", orderId="string", email="string", contact="string", captured="boolean", createdAt="integer"),
        "Order": E(id="string", amount="integer", currency="string", status="string", receipt="string", attempts="integer", createdAt="integer"),
        "Refund": E(id="string", amount="integer", currency="string", status="string", speed="string", paymentId="string", createdAt="integer"),
        "Customer": E(id="string", name="string", email="string", contact="string", createdAt="integer"),
        "Settlement": E(id="string", amount="integer", status="string", fees="integer", tax="integer", createdAt="integer"),
    },
    # Faithful CircleCI v2 model — fields verified against the official
    # circleci.com/api/v2/openapi.json; enum sets NOT enforced (the fetch returned
    # a reduced status set vs the documented one — enforcing it would false-reject).
    "circleci": {
        "Pipeline": E(id="string", number="integer", state="string", projectSlug="string", createdAt="datetime", updatedAt="datetime"),
        "Workflow": E(id="string", pipelineId="string", name="string", status="string", startedBy="string", createdAt="datetime", stoppedAt="datetime"),
        "Job": E(id="string", jobNumber="integer", name="string", status="string", duration="integer", workflowId="string", createdAt="datetime", stoppedAt="datetime"),
        "Project": E(id="string", slug="string", name="string", externalUrl="string"),
        "User": E(id="string", login="string", name="string", avatarUrl="string"),
    },
    # Faithful Linode API v4 model — verified against the official Linode OpenAPI
    # (github.com/linode/linode-api-openapi). snake_case -> camelCase.
    "linode": {
        "Instance": E(id="integer", label="string", status="string", region="string", type="string", image="string", created="datetime", updated="datetime"),
        "Volume": E(id="integer", label="string", status="string", size="integer", region="string", encryption="string", created="datetime", updated="datetime"),
        "Domain": E(id="integer", domain="string", type="string", status="string", soaEmail="string", created="datetime"),
        "NodeBalancer": E(id="integer", label="string", type="string", region="string", ipv4="string", ipv6="string", created="datetime", updated="datetime"),
        "LKECluster": E(id="integer", label="string", region="string", k8sVersion="string", tier="string", created="datetime", updated="datetime"),
        "Image": E(id="string", label="string", status="string", type="string", size="integer", isPublic="boolean", created="datetime", updated="datetime"),
    },
    # Faithful Heroku Platform API model — verified against the official Heroku
    # schema (api.heroku.com/schema). snake_case -> camelCase.
    "heroku": {
        "App": E(id="string", name="string", webUrl="string", createdAt="datetime", updatedAt="datetime"),
        "Dyno": E(id="string", name="string", state="string", command="string", type="string", createdAt="datetime"),
        "Release": E(id="string", version="integer", description="string", current="boolean", createdAt="datetime"),
        "Addon": E(id="string", name="string", state="string", plan="string", app="string", createdAt="datetime"),
        "Build": E(id="string", status="string", app="string", createdAt="datetime", updatedAt="datetime"),
        "Formation": E(id="string", quantity="integer", size="string", type="string", createdAt="datetime"),
    },
    # Faithful Fastly model — fields verified against official Fastly API docs
    # (developer.fastly.com). PARTIAL: Fastly docs publish no closed enum arrays.
    "fastly": {
        "Service": E(id="string", name="string", type="string", customerId="string", comment="string", paused="boolean", createdAt="datetime", updatedAt="datetime"),
        "Version": E(id="string", serviceId="string", number="integer", active="boolean", locked="boolean", deployed="boolean", staging="boolean", comment="string", createdAt="datetime"),
        "Backend": E(name="string", serviceId="string", versionNumber="integer", hostname="string", port="integer", comment="string"),
        "Domain": E(id="string", serviceId="string", fqdn="string", description="string", createdAt="datetime", updatedAt="datetime"),
        "Dictionary": E(name="string", serviceId="string", versionNumber="integer", description="string", createdAt="datetime", updatedAt="datetime"),
    },
    # Faithful Algolia model — verified against the official Algolia OpenAPI
    # (github.com/algolia/api-clients-automation specs/). Array/object fields dropped.
    "algolia": {
        "Index": E(name="string", entries="integer", dataSize="integer", fileSize="integer", lastBuildTimeS="integer", numberOfPendingTasks="integer", pendingTask="boolean", virtual="boolean", createdAt="datetime", updatedAt="datetime"),
        "ApiKey": E(value="string", description="string", maxHitsPerQuery="integer", maxQueriesPerIPPerHour="integer", validity="integer"),
        "Synonym": E(objectID="string", type="string", input="string", word="string", placeholder="string", replacements="string"),
        "Rule": E(objectID="string", description="string", enabled="boolean"),
        "Task": E(taskID="integer", status="string"),
    },
    # Faithful Bitbucket Cloud model — verified against the official Bitbucket
    # swagger (api.bitbucket.org/swagger.json). snake_case->camelCase.
    "bitbucket": {
        "PullRequest": E(id="integer", title="string", state="string", draft="boolean", createdOn="datetime"),
        "Repository": E(name="string", fullName="string", scm="string", isPrivate="boolean", uuid="string", createdOn="datetime"),
        "Workspace": E(name="string", slug="string", uuid="string", isPrivate="boolean", createdOn="datetime"),
        "Project": E(name="string", key="string", uuid="string", isPrivate="boolean", createdOn="datetime"),
        "Issue": E(id="integer", title="string", state="string", priority="string", kind="string", createdOn="datetime"),
        "Commit": E(hash="string", message="string", date="datetime", summary="string", author="string"),
    },
    # Faithful Contentful model — verified against the official CMA docs +
    # contentful-management.js SDK. sys.* flattened; localized/link objects dropped.
    "contentful": {
        "Entry": E(id="string", type="string", version="integer", space="string", environment="string", contentType="string", publishedVersion="integer", createdAt="datetime", updatedAt="datetime", publishedAt="datetime"),
        "Asset": E(id="string", type="string", version="integer", space="string", environment="string", publishedVersion="integer", createdAt="datetime", updatedAt="datetime", publishedAt="datetime"),
        "ContentType": E(id="string", type="string", version="integer", name="string", displayField="string", description="string", createdAt="datetime", updatedAt="datetime"),
        "Space": E(id="string", type="string", version="integer", name="string", organization="string", createdAt="datetime", updatedAt="datetime"),
        "Environment": E(id="string", type="string", version="integer", name="string", space="string", status="string", createdAt="datetime", updatedAt="datetime"),
        "Locale": E(id="string", type="string", version="integer", name="string", code="string", fallbackCode="string", default="boolean", optional="boolean", createdAt="datetime"),
    },
    # Faithful Binance Spot model — verified against the official spec
    # (github.com/binance/binance-spot-api-docs rest-api.md + enums.md).
    # prices/qty are decimal strings; timestamps are integer ms.
    "binance": {
        "Order": E(symbol="string", orderId="integer", clientOrderId="string", price="string", origQty="string", executedQty="string", cummulativeQuoteQty="string", status="string", type="string", side="string", timeInForce="string", transactTime="integer"),
        "Trade": E(id="integer", symbol="string", orderId="integer", price="string", qty="string", quoteQty="string", commission="string", commissionAsset="string", time="integer", isBuyer="boolean", isMaker="boolean"),
        "Balance": E(asset="string", free="string", locked="string"),
        "Account": E(makerCommission="integer", takerCommission="integer", canTrade="boolean", canWithdraw="boolean", canDeposit="boolean", updateTime="integer"),
        "Ticker": E(symbol="string", lastPrice="string", priceChange="string", priceChangePercent="string", highPrice="string", lowPrice="string", volume="string", quoteVolume="string", openTime="integer", closeTime="integer"),
        "Kline": E(openTime="integer", open="string", high="string", low="string", close="string", volume="string", closeTime="integer", trades="integer"),
    },
    # Faithful Shippo model — verified against the official Shippo OpenAPI + SDK
    # (docs.goshippo.com + goshippo/shippo-node-sdk). Object/array fields dropped.
    "shippo": {
        "Address": E(name="string", company="string", street1="string", city="string", state="string", zip="string", country="string", phone="string", email="string", isResidential="boolean"),
        "Parcel": E(objectId="string", weight="string", massUnit="string", length="string", width="string", height="string", distanceUnit="string", objectCreated="datetime"),
        "Shipment": E(objectId="string", status="string", addressFrom="string", addressTo="string", shipmentDate="datetime", objectCreated="datetime"),
        "Rate": E(objectId="string", amount="string", currency="string", carrierAccount="string", servicelevelToken="string", estimatedDays="integer", objectCreated="datetime"),
        "Transaction": E(objectId="string", status="string", objectState="string", trackingNumber="string", trackingStatus="string", labelUrl="string", labelFileType="string", rate="string", test="boolean", objectCreated="datetime"),
        "TrackingStatus": E(objectId="string", status="string", statusDetails="string", substatus="string", statusDate="datetime"),
    },
    # Faithful Trello model — verified against the official Trello swagger
    # (dac-static.atlassian.com/cloud/trello/swagger.v3.json). Array fields dropped.
    "trello": {
        "Card": E(id="string", idShort="integer", name="string", desc="string", closed="boolean", due="datetime", dueComplete="boolean", pos="float", url="string", idBoard="string", idList="string", cardRole="string", dateLastActivity="datetime"),
        "Board": E(id="string", name="string", desc="string", closed="boolean", url="string", idOrganization="string", pinned="boolean", starred="boolean", dateLastActivity="datetime"),
        "List": E(id="string", name="string", closed="boolean", pos="float", idBoard="string"),
        "Member": E(id="string", username="string", fullName="string", initials="string", memberType="string", confirmed="boolean"),
        "Label": E(id="string", idBoard="string", name="string", color="string"),
    },
    # Faithful Canva Connect API model — verified against the official OpenAPI
    # (canva-sdks/canva-connect-api-starter-kit spec.yml). Timestamps Unix int seconds.
    "canva": {
        "Design": E(id="string", title="string", pageCount="integer", createdAt="integer", updatedAt="integer"),
        "Asset": E(id="string", name="string", type="string", createdAt="integer", updatedAt="integer"),
        "Folder": E(id="string", name="string", createdAt="integer", updatedAt="integer"),
        "BrandTemplate": E(id="string", title="string", viewUrl="string", createdAt="integer", updatedAt="integer"),
        "ExportJob": E(id="string", status="string", format="string"),
        "User": E(id="string", displayName="string"),
    },
    # Faithful BigCommerce model — verified against the official BigCommerce
    # OpenAPI specs (github.com/bigcommerce/api-specs).
    "bigcommerce": {
        "Product": E(id="integer", name="string", type="string", sku="string", description="string", price="float", availability="string", condition="string", inventoryTracking="string", isVisible="boolean", dateCreated="datetime"),
        "Order": E(id="integer", customerId="integer", email="string", status="string", total="float", subtotal="float", currencyCode="string", paymentMethod="string", dateCreated="datetime"),
        "Customer": E(id="integer", email="string", firstName="string", lastName="string", company="string", phone="string", customerGroupId="integer", dateCreated="datetime"),
        "Category": E(id="integer", name="string", parentId="integer", description="string", isVisible="boolean", sortOrder="integer", defaultProductSort="string"),
        "Brand": E(id="integer", name="string", pageTitle="string", searchKeywords="string", imageUrl="string"),
        "Cart": E(id="string", customerId="integer", email="string", channelId="integer", baseAmount="float", cartAmount="float", createdTime="datetime"),
    },
    # Faithful LaunchDarkly model — verified against the official OpenAPI
    # (github.com/launchdarkly/ld-openapi). _id->id; Member.role left a gap.
    "launchdarkly": {
        "FeatureFlag": E(key="string", name="string", kind="string", description="string", temporary="boolean", archived="boolean"),
        "Project": E(id="string", key="string", name="string", includeInSnippetByDefault="boolean"),
        "Environment": E(id="string", key="string", name="string", apiKey="string", mobileKey="string", color="string"),
        "Segment": E(key="string", name="string", environmentKey="string", description="string", deleted="boolean", creationDate="integer"),
        "Member": E(id="string", email="string", firstName="string", lastName="string", role="string"),
        "Webhook": E(id="string", name="string", url="string", on="boolean"),
    },
    # Faithful WooCommerce REST v3 model — verified against the official docs
    # (woocommerce.github.io/woocommerce-rest-api-docs).
    "woocommerce": {
        "Order": E(id="integer", number="string", orderKey="string", status="string", currency="string", total="float", totalTax="float", discountTotal="float", customerId="integer", dateCreated="datetime"),
        "Product": E(id="integer", name="string", slug="string", type="string", status="string", featured="boolean", catalogVisibility="string", sku="string", regularPrice="float", salePrice="float", onSale="boolean", stockQuantity="integer", stockStatus="string", virtual="boolean", downloadable="boolean"),
        "Customer": E(id="integer", email="string", firstName="string", lastName="string", username="string", role="string", isPayingCustomer="boolean", dateCreated="datetime"),
        "Coupon": E(id="integer", code="string", amount="float", discountType="string", description="string", individualUse="boolean", freeShipping="boolean", minimumAmount="float"),
        "ProductCategory": E(id="integer", name="string", slug="string", parent="integer", description="string", display="string", menuOrder="integer"),
        "Refund": E(id="integer", amount="float", reason="string", refundedBy="integer", refundedPayment="boolean", dateCreated="datetime"),
    },
    # Faithful Mux Video model — verified against official Mux docs. Asset/PlaybackId/
    # Track fully confirmed; Upload/LiveStream status not accessible -> gaps.
    "mux": {
        "Asset": E(id="string", status="string", duration="float", resolutionTier="string", videoQuality="string", aspectRatio="string", test="boolean", createdAt="integer"),
        "PlaybackId": E(id="string", policy="string"),
        "Track": E(id="string", type="string", duration="float", maxWidth="integer", maxHeight="integer", status="string", primary="boolean"),
        "Upload": E(id="string", status="string", timeout="integer", test="boolean"),
        "LiveStream": E(id="string", status="string", latencyMode="string"),
    },
    # Faithful Netlify model — verified against the official Netlify OpenAPI
    # (github.com/netlify/open-api swagger.yml). Object fields dropped.
    "netlify": {
        "Site": E(id="string", name="string", url="string", sslUrl="string", adminUrl="string", state="string", customDomain="string", accountId="string", ssl="boolean", forceSsl="boolean", createdAt="datetime", updatedAt="datetime"),
        "Deploy": E(id="string", siteId="string", url="string", state="string", draft="boolean", branch="string", commitRef="string", locked="boolean", createdAt="datetime", publishedAt="datetime"),
        "Build": E(id="string", deployId="string", sha="string", done="boolean", error="string", createdAt="datetime"),
        "DnsZone": E(id="string", siteId="string", domain="string", dedicated="boolean", ipv6Enabled="boolean", accountId="string", createdAt="datetime"),
        "Hook": E(id="string", siteId="string", type="string", event="string", disabled="boolean", createdAt="datetime"),
        "Form": E(id="string", siteId="string", name="string", submissionCount="integer", createdAt="datetime"),
    },
    # Faithful Supabase Management API model — verified against the live OpenAPI
    # (api.supabase.com/api/v1-json). _id->id; snake_case->camelCase.
    "supabase": {
        "Project": E(id="string", ref="string", organizationSlug="string", name="string", region="string", status="string", createdAt="datetime"),
        "Organization": E(id="string", slug="string", name="string"),
        "EdgeFunction": E(id="string", slug="string", name="string", status="string", version="integer", verifyJwt="boolean", entrypointPath="string", createdAt="integer", updatedAt="integer"),
        "ApiKey": E(id="string", type="string", name="string", description="string", prefix="string", insertedAt="datetime", updatedAt="datetime"),
        "Branch": E(id="string", name="string", projectRef="string", parentProjectRef="string", isDefault="boolean", persistent="boolean", status="string", previewProjectStatus="string", createdAt="datetime"),
        "Backup": E(id="integer", status="string", isPhysicalBackup="boolean", insertedAt="datetime"),
    },
    # Faithful OpenAI model — verified against the official OpenAPI
    # (github.com/openai/openai-openapi openapi.yaml). timestamps Unix int seconds.
    "openai": {
        "Model": E(id="string", object="string", created="integer", ownedBy="string"),
        "FineTuningJob": E(id="string", model="string", status="string", fineTunedModel="string", createdAt="integer", finishedAt="integer"),
        "Batch": E(id="string", object="string", endpoint="string", model="string", status="string", inputFileId="string", createdAt="integer"),
        "File": E(id="string", bytes="integer", filename="string", object="string", purpose="string", status="string", createdAt="integer"),
        "Embedding": E(index="integer", object="string"),
        "ChatCompletion": E(id="string", model="string", object="string", created="integer"),
    },
    # Faithful Typeform model — verified against the official Typeform Create +
    # Responses API docs. Object/array fields dropped.
    "typeform": {
        "Form": E(id="string", title="string", type="string"),
        "Field": E(ref="string", id="string", title="string", type="string"),
        "Response": E(token="string", landedAt="datetime", submittedAt="datetime", formId="string"),
        "Answer": E(fieldId="string", fieldType="string", type="string", value="string"),
        "Webhook": E(eventId="string", eventType="string", timestamp="datetime"),
    },
    # Faithful ElevenLabs model — verified against the live official OpenAPI
    # (api.elevenlabs.io/openapi.json). timestamps Unix int seconds.
    "elevenlabs": {
        "Voice": E(voiceId="string", name="string", category="string", description="string", previewUrl="string", createdAtUnix="integer", isOwner="boolean"),
        "Sample": E(sampleId="string", fileName="string", mimeType="string", sizeBytes="integer", durationSecs="float", hash="string", removeBackgroundNoise="boolean"),
        "HistoryItem": E(historyItemId="string", voiceId="string", modelId="string", text="string", dateUnix="integer", state="string", characterCountChangeTo="integer", contentType="string"),
        "Model": E(modelId="string", name="string", canBeFinetune="boolean", canDoTextToSpeech="boolean", canUseStyle="boolean", tokenCostFactor="float", description="string"),
        "Subscription": E(tier="string", characterCount="integer", characterLimit="integer", voiceSlotsUsed="integer", voiceLimit="integer", status="string", canExtendCharacterLimit="boolean"),
        "Project": E(projectId="string", name="string", title="string", author="string", createDateUnix="integer", state="string", accessLevel="string", canBeDownloaded="boolean"),
    },
    # Faithful Grafana HTTP API model — verified against the official Grafana docs.
    # Only DataSource.access enforced (alert-state enums are version-dependent).
    "grafana": {
        "Dashboard": E(id="integer", uid="string", title="string", schemaVersion="integer", version="integer", editable="boolean", timezone="string"),
        "DataSource": E(id="integer", uid="string", name="string", type="string", access="string", url="string", isDefault="boolean"),
        "Folder": E(uid="string", name="string", title="string", resourceVersion="string", creationTimestamp="datetime"),
        "AlertRule": E(uid="string", title="string", condition="string", noDataState="string", execErrState="string", isPaused="boolean"),
        "User": E(id="integer", email="string", name="string", login="string", isGrafanaAdmin="boolean", isDisabled="boolean"),
        "Organization": E(id="integer", name="string", address="string"),
    },
    # Faithful Webflow Data API v2 model — verified against the official OpenAPI
    # (github.com/webflow/openapi-spec). Object/array fields dropped.
    "webflow": {
        "Site": E(id="string", displayName="string", shortName="string", timeZone="string", createdOn="datetime", lastUpdated="datetime", lastPublished="datetime"),
        "Collection": E(id="string", displayName="string", singularName="string", slug="string", createdOn="datetime", lastUpdated="datetime"),
        "CollectionItem": E(id="string", cmsLocaleId="string", isArchived="boolean", isDraft="boolean", createdOn="datetime", lastUpdated="datetime", lastPublished="datetime"),
        "Page": E(id="string", siteId="string", title="string", slug="string", archived="boolean", draft="boolean", publishedPath="string", parentId="string", createdOn="datetime", lastUpdated="datetime"),
        "Form": E(id="string", displayName="string", siteId="string", pageId="string", pageName="string", formElementId="string", createdOn="datetime", lastUpdated="datetime"),
        "Field": E(id="string", displayName="string", slug="string", type="string", isRequired="boolean"),
    },
    # Faithful Bandwidth model — verified against the OFFICIAL Bandwidth repo
    # (github.com/Bandwidth/api-docs). Only enums both official sources agree on are
    # enforced (directions + fileFormat); disputed lifecycle enums left as gaps.
    "bandwidth": {
        "Message": E(id="string", owner="string", applicationId="string", time="datetime", segmentCount="integer", direction="string", toNumber="string", fromNumber="string", text="string", tag="string"),
        "Call": E(callId="string", accountId="string", applicationId="string", toNumber="string", fromNumber="string", state="string", direction="string", createdTime="datetime", startTime="datetime", endTime="datetime"),
        "Conference": E(id="string", name="string", status="string", redirectUrl="string", createdTime="datetime"),
        "Recording": E(recordingId="string", applicationId="string", accountId="string", name="string", status="string", fileFormat="string", startTime="datetime", endTime="datetime", duration="integer"),
    },
    # Faithful Fivetran model — verified against the official Fivetran REST API docs.
    # Nested status.* flattened. User.role left open (custom roles allowed).
    "fivetran": {
        "Connector": E(id="string", service="string", schema="string", groupId="string", setupState="string", syncState="string", updateState="string", scheduleType="string", networkingMethod="string", syncFrequency="integer", paused="boolean", createdAt="datetime", succeededAt="datetime", failedAt="datetime"),
        "Destination": E(id="string", groupId="string", service="string", region="string", setupStatus="string", networkingMethod="string", daylightSavingTimeEnabled="boolean", createdAt="datetime"),
        "Group": E(id="string", name="string", createdAt="datetime"),
        "User": E(id="string", email="string", givenName="string", familyName="string", role="string", verified="boolean", active="boolean", createdAt="datetime"),
        "Transformation": E(id="string", type="string", status="string", paused="boolean", createdAt="datetime", lastStartedAt="datetime", lastEndedAt="datetime"),
    },
    # Faithful Cohere model — verified against official docs.cohere.com. Only the 3
    # confirmed entities modeled (EmbedJob/FineTunedModel/Connector 404'd -> deferred).
    "cohere": {
        "Dataset": E(id="string", name="string", validationStatus="string", datasetType="string", createdAt="datetime"),
        "DatasetPart": E(id="string", name="string", sizeBytes="integer", numRows="integer"),
        "Model": E(name="string", isDeprecated="boolean", contextLength="integer", finetuned="boolean"),
    },
    # Faithful SonarQube Web API model — verified against official SonarSource docs.
    "sonarqube": {
        "Issue": E(key="string", severity="string", status="string", type="string", resolution="string", component="string", line="integer", message="string"),
        "Hotspot": E(key="string", status="string", message="string", component="string"),
        "QualityGate": E(status="string", ignoredConditions="boolean"),
        "Condition": E(status="string", metricKey="string", comparator="string", errorThreshold="string", actualValue="string"),
        "Measure": E(metric="string", value="string", bestValue="boolean"),
    },
    # Faithful Terraform Cloud / HCP Terraform API model — verified against the
    # official HashiCorp Cloud API docs. JSON:API attributes flattened.
    "terraform": {
        "Run": E(id="string", type="string", status="string", message="string", source="string", triggerReason="string", hasChanges="boolean", autoApply="boolean", isDestroy="boolean", planOnly="boolean", createdAt="datetime", canceledAt="datetime"),
        "Plan": E(id="string", type="string", status="string", hasChanges="boolean", resourceAdditions="integer", resourceChanges="integer", resourceDestructions="integer"),
        "Apply": E(id="string", type="string", status="string", resourceAdditions="integer", resourceChanges="integer", resourceDestructions="integer"),
        "Workspace": E(id="string", name="string", type="string", description="string", executionMode="string", locked="boolean", resourceCount="integer", autoApply="boolean", terraformVersion="string", createdAt="datetime", updatedAt="datetime"),
        "StateVersion": E(id="string", status="string", serial="integer", terraformVersion="string", resourcesProcessed="boolean", createdAt="datetime"),
        "ConfigurationVersion": E(id="string", type="string", status="string", source="string", speculative="boolean", provisional="boolean", autoQueueRuns="boolean"),
    },
    # Faithful Jenkins Remote Access API model — verified against the official
    # Jenkins core source (@Exported fields + Result/BallColor enums).
    "jenkins": {
        "Build": E(number="integer", result="string", building="boolean", duration="integer", timestamp="integer", displayName="string", description="string", id="string", queueId="integer"),
        "Job": E(name="string", displayName="string", description="string", color="string", nextBuildNumber="integer", url="string"),
        "QueueItem": E(id="integer", inQueueSince="integer", why="string", blocked="boolean", buildable="boolean", stuck="boolean"),
        "Computer": E(displayName="string", name="string", url="string", offline="boolean", offlineCauseReason="string", numExecutors="integer"),
        "View": E(name="string", url="string", description="string"),
    },
    # Faithful Elasticsearch model — verified against official Elastic.co reference docs.
    "elastic": {
        "ClusterHealth": E(clusterName="string", status="string", numberOfNodes="integer", numberOfDataNodes="integer", activePrimaryShards="integer", activeShards="integer", relocatingShards="integer", initializingShards="integer", unassignedShards="integer", timedOut="boolean"),
        "Index": E(name="string", health="string", status="string", uuid="string", numberOfShards="integer", numberOfReplicas="integer", docsCount="integer", docsDeleted="integer", storeSize="string"),
        "Shard": E(index="string", shardNumber="integer", primaryOrReplica="string", state="string", docsCount="integer", nodeName="string", nodeId="string"),
        "Node": E(id="string", ip="string", port="integer", name="string", version="string", heapPercent="integer", ramPercent="integer", diskUsedPercent="integer", master="string"),
        "Alias": E(alias="string", index="string", routingIndex="string", routingSearch="string", isWriteIndex="string"),
        "Document": E(index="string", id="string", version="integer", seqNo="integer", primaryTerm="integer", found="boolean", routing="string"),
    },
    # Faithful Pulumi Cloud model — verified against the official Pulumi Go SDK
    # apitype package (github.com/pulumi/pulumi). Organization.role left open.
    "pulumi": {
        "Update": E(kind="string", result="string", message="string", version="integer", resourceCount="integer", startTime="integer", endTime="integer"),
        "Stack": E(stackName="string", orgName="string", projectName="string", id="string", lastUpdate="integer", resourceCount="integer"),
        "Policy": E(name="string", displayName="string", description="string", enforcementLevel="string", severity="string", message="string"),
        "Deployment": E(id="string", status="string", projectName="string", stackName="string", paused="boolean", created="datetime", modified="datetime"),
        "Organization": E(name="string", role="string"),
    },
    # Faithful SS7/SIGTRAN model — M3UA (RFC 4666) + SUA (RFC 3868) message classes
    # are RFC-verified closed sets; SCCP/ISUP message types are ITU-T-paywalled -> gapped.
    "ss7_sigtran": {
        "M3uaMessage": E(version="integer", reserved="integer", messageClass="integer", messageType="integer", messageLength="integer"),
        "SuaMessage": E(version="integer", messageClass="integer", messageType="integer", messageLength="integer"),
        "ProtocolData": E(opc="integer", dpc="integer", si="integer", ni="integer", mp="integer", sls="integer"),
        "Mtp3Message": E(serviceIndicator="integer", networkIndicator="integer", payload="string"),
        "SccpMessage": E(messageType="integer", destinationPointCode="integer", sourcePointCode="integer", subsystemNumber="integer", globalTitle="string"),
    },
    # Faithful CVE/NVD + CVSS v3.1 model — verified vs the FIRST CVSS v3.1 spec +
    # the official NIST NVD API schema. All CVSS metric value sets are closed.
    "cve_nvd": {
        "CveItem": E(cveId="string", sourceIdentifier="string", vulnStatus="string", published="datetime", lastModified="datetime"),
        "CvssV3Metric": E(baseScore="float", baseSeverity="string", exploitabilityScore="float", impactScore="float"),
        "CvssV3Vector": E(version="string", vectorString="string", attackVector="string", attackComplexity="string", privilegesRequired="string", userInteraction="string", scope="string", confidentialityImpact="string", integrityImpact="string", availabilityImpact="string"),
        "Reference": E(url="string", source="string"),
        "Weakness": E(source="string", type="string", description="string"),
        "CveMetrics": E(source="string", type="string"),
    },
    # Faithful MITRE ATT&CK model — verified vs the official attack-stix-data. Only
    # Software.type (closed STIX object set) enforced; Tactic.shortName fetch was
    # contaminated (bogus values) -> gapped rather than enforce a corrupted set.
    "mitre_attck": {
        "Technique": E(techniqueId="string", name="string", description="string", isSubtechnique="boolean", created="datetime", modified="datetime"),
        "Tactic": E(tacticId="string", shortName="string", name="string", description="string", created="datetime"),
        "Software": E(softwareId="string", name="string", type="string", description="string", isFamily="boolean", created="datetime"),
        "Group": E(groupId="string", name="string", description="string", created="datetime"),
        "Mitigation": E(mitigationId="string", name="string", description="string", deprecated="boolean", created="datetime"),
    },
    # Faithful WebRTC model — verified against the official W3C WebRTC 1.0 spec.
    "webrtc_core": {
        "RTCPeerConnection": E(signalingState="string", iceConnectionState="string", iceGatheringState="string", connectionState="string"),
        "RTCDataChannel": E(label="string", ordered="boolean", protocol="string", negotiated="boolean", id="integer", readyState="string", bufferedAmount="integer"),
        "RTCSessionDescription": E(type="string", sdp="string"),
        "RTCIceCandidate": E(candidate="string", sdpMLineIndex="integer", sdpMid="string", protocol="string", port="integer", address="string", type="string", tcpType="string", priority="integer"),
        "RTCRtpTransceiver": E(mid="string", direction="string", currentDirection="string"),
    },
    # Faithful QUIC (RFC 9000) + HTTP/3 (RFC 9114) model — verified vs RFC + IANA.
    # Http3Settings.identifier is an open registry -> not enforced.
    "quic_http3": {
        "QuicPacket": E(packetType="string", version="integer", sourceConnectionId="string", destinationConnectionId="string", payloadLength="integer", packetNumber="integer"),
        "QuicFrame": E(frameType="integer", payload="string", streamId="integer", offsetInStream="integer"),
        "Http3Frame": E(frameType="integer", length="integer", payload="string"),
        "Http3Settings": E(identifier="integer", value="integer"),
        "QuicConnection": E(connectionId="string", version="integer", state="string", createdAt="datetime", lastActivityAt="datetime"),
    },
    # Faithful RPKI model (RFC 6811 origin validation + RFC 6482 ROA + RFC 8210 RPKI-Router).
    # validationState (valid/invalid/not-found) is the closed RFC 6811 §2 set; pduType is the
    # fully-enumerated RFC 8210 §5 set (type 5 unassigned). PrefixPdu.flags is a bitfield -> gapped.
    "bgp_rpki": {
        "RouteOriginAuthorization": E(version="integer", asn="integer", prefix="string", prefixLength="integer", maxLength="integer", addressFamily="string"),
        "ValidationResult": E(asn="integer", prefix="string", prefixLength="integer", validationState="string"),
        "RpkiToRouterPdu": E(protocolVersion="integer", pduType="integer", sessionId="integer", serialNumber="integer", length="integer"),
        "PrefixPdu": E(protocolVersion="integer", pduType="integer", flags="integer", prefixLength="integer", maxLength="integer", prefix="string", asn="integer"),
    },
    # Faithful CAN bus model (ISO 11898 / Bosch CAN 2.0 + CAN FD). frameType, format, errorType,
    # errorFlag, nodeState are documented closed sets. CanFdFrame.frameType gapped (FD remote-frame
    # nuance); dlc is a numeric field (0-8 classic / 0-15 FD) -> not an enum.
    "can_bus": {
        "CanFrame": E(identifier="integer", frameType="string", format="string", dlc="integer", rtr="boolean", data="string", crc="integer"),
        "CanFdFrame": E(identifier="integer", frameType="string", format="string", dlc="integer", brs="boolean", esi="boolean", data="string", crc="integer"),
        "ErrorFrame": E(errorType="string", errorFlag="string", transmitErrorCounter="integer", receiveErrorCounter="integer", nodeState="string"),
        "RemoteFrame": E(identifier="integer", format="string", dlc="integer", rtr="boolean"),
        "OverloadFrame": E(overloadFlag="string", timestamp="datetime"),
    },
    # Faithful OPC UA model (IEC 62541, OPC Foundation UA-Nodeset Opc.Ua.Types.bsd +
    # AttributeIds.csv). nodeClass (bitmask 0..128), attributeId (1..27), monitoringMode
    # (0..2), timestampsToReturn (0..4) are documented closed integer enums.
    "opc_ua": {
        "Node": E(nodeId="string", nodeClass="integer", browseName="string", displayName="string", description="string", writeMask="integer", accessLevel="integer", valueRank="integer", historizing="boolean"),
        "ReferenceDescription": E(referenceTypeId="string", isForward="boolean", nodeId="string", browseName="string", displayName="string", nodeClass="integer", typeDefinition="string"),
        "ReadValueId": E(nodeId="string", attributeId="integer", indexRange="string", dataEncoding="string"),
        "MonitoredItem": E(clientHandle="integer", monitoringMode="integer", samplingInterval="float", queueSize="integer", discardOldest="boolean"),
        "CreateSubscriptionRequest": E(requestedPublishingInterval="float", requestedLifetimeCount="integer", requestedMaxKeepAliveCount="integer", maxNotificationsPerPublish="integer", publishingEnabled="boolean", priority="integer"),
        "ReadRequest": E(maxAge="float", timestampsToReturn="integer"),
    },
    # Faithful Redis RESP model (redis.io official protocol-spec + TYPE command). firstByte
    # is the definitively-closed RESP3 first-byte marker set (superset of RESP2). dataType is
    # the TYPE-command return set (inclusive of newer vectorset to avoid false-reject). Command
    # flags are an open/extensible set -> not enforced.
    "redis": {
        "RespMessage": E(firstByte="string", respType="string", payload="string", elementCount="integer", length="integer"),
        "RedisCommand": E(commandName="string", arity="integer", flags="string", keyPosition="integer"),
        "RedisKey": E(keyName="string", dataType="string", ttl="integer", encoding="string"),
        "RedisDataType": E(dataType="string", encoding="string", isBinary="boolean"),
        "RespProtocolVersion": E(majorVersion="integer", supportedSince="string"),
    },
    # Faithful TCP/IP model (RFC 9293 TCP + RFC 792 ICMP + IANA). ICMP type + IP protocol
    # are large extensible IANA registries -> not enforced as closed enums.
    "tcp_ip": {
        "TcpSegment": E(sourcePort="integer", destinationPort="integer", sequenceNumber="integer", acknowledgmentNumber="integer", dataOffset="integer", controlBits="string", window="integer", urgentPointer="integer"),
        "TcpConnection": E(localPort="integer", remotePort="integer", state="string", sequenceSendNext="integer", sequenceReceiveNext="integer"),
        "IpPacket": E(version="integer", headerLength="integer", totalLength="integer", identification="integer", flags="string", fragmentOffset="integer", timeToLive="integer", protocol="integer", sourceAddress="string", destinationAddress="string"),
        "IcmpMessage": E(type="integer", code="integer", checksum="string", restOfHeader="string"),
    },
    # Faithful DNS model (RFC 1035 + IANA dns-parameters). rrType/qtype are open
    # extensible registries + rcode is EDNS-extensible -> not enforced as closed enums.
    "dns_root_zone": {
        "Header": E(id="integer", qr="boolean", opcode="integer", aa="boolean", tc="boolean", rd="boolean", ra="boolean", rcode="integer", qdcount="integer", ancount="integer", nscount="integer", arcount="integer"),
        "Question": E(qname="string", qtype="integer", qclass="integer"),
        "ResourceRecord": E(name="string", type="integer", class_="integer", ttl="integer", rdlength="integer", rdata="string"),
        "OptRecord": E(extendedRcode="integer", version="integer", flags="integer", rdlength="integer"),
    },
    # Faithful IPsec / IKEv2 model (RFC 7296 + IANA ikev2-parameters). Per-type transform
    # IDs + the large Notify-type registry are volatile -> not enforced as closed enums.
    "ipsec": {
        "IkeHeader": E(initiatorSpi="integer", responderSpi="integer", nextPayload="integer", majorVersion="integer", minorVersion="integer", exchangeType="integer", flags="integer", messageId="integer", totalLength="integer"),
        "Payload": E(nextPayload="integer", critical="boolean", payloadLength="integer", payloadType="integer"),
        "SecurityAssociation": E(payloadType="integer", proposals="integer"),
        "Proposal": E(number="integer", protocolId="integer", spiSize="integer", transformCount="integer", spi="string"),
        "Transform": E(type="integer", transformId="integer", transformLength="integer", attributes="string"),
        "Notify": E(protocolId="integer", spiSize="integer", notifyMessageType="integer", spi="string", notificationData="string"),
    },
    # Faithful GTFS Schedule model — verified vs gtfs.org/schedule/reference. Many
    # small closed integer enums. (newer/experimental carsAllowed/cemvSupport excluded.)
    "gtfs": {
        "Agency": E(agencyId="string", agencyName="string", agencyUrl="string", agencyTimezone="string", agencyLang="string", agencyPhone="string", agencyEmail="string"),
        "Route": E(routeId="string", agencyId="string", routeShortName="string", routeLongName="string", routeDesc="string", routeType="integer", routeColor="string", routeSortOrder="integer", continuousPickup="integer", continuousDropOff="integer"),
        "Trip": E(routeId="string", serviceId="string", tripId="string", tripHeadsign="string", directionId="integer", blockId="string", shapeId="string", wheelchairAccessible="integer", bikesAllowed="integer"),
        "Stop": E(stopId="string", stopCode="string", stopName="string", stopDesc="string", stopLat="float", stopLon="float", zoneId="string", locationType="integer", parentStation="string", wheelchairBoarding="integer"),
        "StopTime": E(tripId="string", arrivalTime="datetime", departureTime="datetime", stopId="string", stopSequence="integer", pickupType="integer", dropOffType="integer", timepoint="integer", shapeDistTraveled="float"),
        "Transfer": E(fromStopId="string", toStopId="string", transferType="integer", minTransferTime="integer"),
    },
    # Faithful UN/LOCODE model — function classifier is a closed UNECE set; status codes
    # gapped (UNECE site 403; public reference may be incomplete).
    "un_locode": {
        "Location": E(countryCode="string", locationCode="string", name="string", nameWoDiacritics="string", function="string", status="string", subdivision="string", iataCode="string", latitude="float", longitude="float"),
        "FunctionClassifier": E(code="string", definition="string"),
        "StatusCode": E(code="string", definition="string"),
    },
    # Faithful OMOP CDM v5.4 (OHDSI) model — verified vs ohdsi.github.io/CommonDataModel.
    # *_concept_id fields are CONCEPT-table vocab refs (not enums) -> not enforced.
    "omop_cdm": {
        "Person": E(personId="integer", genderConceptId="integer", yearOfBirth="integer", monthOfBirth="integer", dayOfBirth="integer", birthDatetime="datetime", raceConceptId="integer", ethnicityConceptId="integer"),
        "Concept": E(conceptId="integer", conceptName="string", domainId="string", vocabularyId="string", conceptClassId="string", standardConcept="string", conceptCode="string", validStartDate="datetime", validEndDate="datetime", invalidReason="string"),
        "ConditionOccurrence": E(conditionOccurrenceId="integer", personId="integer", conditionConceptId="integer", conditionStartDate="datetime", conditionEndDate="datetime", visitOccurrenceId="integer"),
        "DrugExposure": E(drugExposureId="integer", personId="integer", drugConceptId="integer", drugExposureStartDate="datetime", quantity="float", daysSupply="integer"),
        "VisitOccurrence": E(visitOccurrenceId="integer", personId="integer", visitConceptId="integer", visitStartDate="datetime", visitEndDate="datetime", providerId="integer"),
        "Observation": E(observationId="integer", personId="integer", observationConceptId="integer", observationDate="datetime", valueAsNumber="float", valueAsString="string"),
    },
    # Faithful eIDAS model — levelOfAssurance is the closed Art.8 Reg 910/2014 set;
    # SAML attrname-format is closed. serviceType/classRef/status not exhaustive -> gapped.
    "eidas": {
        "AuthenticationAssertion": E(id="string", levelOfAssurance="string", issueInstant="datetime", sessionIndex="string", issuer="string"),
        "EidasAttribute": E(name="string", friendlyName="string", nameFormat="string", value="string"),
        "TrustService": E(id="string", serviceProvider="string", serviceName="string", serviceType="string", status="string", statusStartingTime="datetime"),
        "Subject": E(nameID="string", format="string", spNameQualifier="string"),
    },
    # Faithful DICOMweb model (DICOM PS3.18). PatientSex (M/F/O) is closed; Modality
    # (large extensible defined-terms) + SOP Class UIDs (huge registry) -> not enforced.
    "dicomweb": {
        "Study": E(studyInstanceUid="string", studyDate="string", studyTime="string", studyDescription="string", accessionNumber="string", referringPhysicianName="string"),
        "Series": E(seriesInstanceUid="string", seriesNumber="integer", seriesDescription="string", modality="string", seriesDate="string"),
        "Instance": E(sopInstanceUid="string", sopClassUid="string", instanceNumber="integer", contentDate="string"),
        "Patient": E(patientId="string", patientName="string", patientBirthDate="string", patientSex="string"),
        "QidoQuery": E(patientId="string", patientName="string", studyInstanceUid="string", modality="string", fuzzyMatching="boolean"),
    },
    # Faithful eClinicalWorks FHIR R4 model — ONC (g)(10)-certified (HL7 product registry
    # product_id=461) exposes HL7 FHIR R4 US Core; normative R4 value sets (hl7.org/fhir/R4).
    "eclinicalworks": {
        "Patient": E(id="string", resourceType="string", gender="string", birthDate="string", active="boolean", deceasedBoolean="boolean"),
        "Observation": E(id="string", resourceType="string", status="string", effectiveDateTime="datetime", valueString="string", issued="datetime"),
        "Encounter": E(id="string", resourceType="string", status="string", serviceType="string", period="string"),
        "MedicationRequest": E(id="string", resourceType="string", status="string", intent="string", authoredOn="datetime"),
        "AllergyIntolerance": E(id="string", resourceType="string", clinicalStatus="string", criticality="string", recordedDate="datetime"),
        "Condition": E(id="string", resourceType="string", clinicalStatus="string", recordedDate="datetime"),
    },
    # Faithful IPv6/ICMPv6 model (RFC 8200 + RFC 4443). version is fixed (6); per-type
    # ICMPv6 code sets are closed. Icmpv6.type (extensible) + nextHeader (protocol registry) gapped.
    "ipv6_routing": {
        "Ipv6Header": E(version="integer", trafficClass="integer", flowLabel="integer", payloadLength="integer", nextHeader="integer", hopLimit="integer"),
        "Icmpv6Message": E(type="integer", code="integer", checksum="integer"),
        "DestinationUnreachable": E(type="integer", code="integer", checksum="integer"),
        "TimeExceeded": E(type="integer", code="integer", checksum="integer"),
        "ParameterProblem": E(type="integer", code="integer", pointer="integer"),
        "NdpMessage": E(type="integer", code="integer", targetAddress="string"),
    },
    # Faithful MPLS model (RFC 3032/3031 + IANA mpls-label-values). General labels
    # 16+ are user-allocated -> not enforced; reserved labels 0-15 + TC + NHLFE ops closed.
    "mpls": {
        "LabelStackEntry": E(label="integer", tc="integer", s="boolean", ttl="integer"),
        "MplsHeader": E(stackDepth="integer", topLabel="integer", trafficClass="integer", bottomOfStack="boolean", timeToLive="integer"),
        "ReservedLabel": E(value="integer", name="string", purpose="string"),
        "NhlfeOperation": E(operationType="string", newLabel="integer", nextHopDestination="string"),
        "MplsForwardingState": E(incomingLabel="integer", fecRef="string", hopCount="integer"),
    },
    # Faithful AIS (ITU-R M.1371) model — verified vs gpsd AIVDM canonical reference.
    # shipType (0-99) is a large IMO code list -> not enforced.
    "ais_marine": {
        "Message": E(messageType="integer", repeatIndicator="integer", mmsi="integer"),
        "PositionReport": E(messageType="integer", mmsi="integer", navigationStatus="integer", rateOfTurn="float", speedOverGround="float", longitude="float", latitude="float", courseOverGround="float", trueHeading="integer", maneuverIndicator="integer"),
        "BaseStationReport": E(messageType="integer", mmsi="integer", longitude="float", latitude="float", typeOfEpfd="integer"),
        "StaticVoyageData": E(messageType="integer", mmsi="integer", imoNumber="integer", callSign="string", vesselName="string", shipType="integer", draught="float", destination="string"),
        "AidToNavigationReport": E(messageType="integer", mmsi="integer", typeOfAid="integer", name="string", longitude="float", latitude="float", typeOfEpfd="integer"),
    },
    # Faithful AS2 (RFC 4130) model — verified vs the official RFC. micalg/digestAlgorithm
    # algorithm sets evolve past RFC 4130 (sha1/md5) -> not enforced; MDN grammar enums are.
    "as2_protocol": {
        "As2Message": E(messageId="string", as2From="string", as2To="string", as2Version="string", contentType="string", micalg="string", contentTransferEncoding="string", dispositionNotificationTo="string"),
        "Mdn": E(messageId="string", originalMessageId="string", finalRecipient="string", dispositionType="string", dispositionMode="string", actionMode="string", sendingMode="string", dispositionModifier="string", digestAlgorithm="string"),
        "DispositionNotification": E(reportingUa="string", finalRecipient="string", originalMessageId="string", disposition="string", receivedContentMic="string"),
    },
    # Faithful BGP-4 (RFC 4271) model — verified against the official RFC 4271 + IANA
    # BGP parameters registry. Enums scoped to RFC 4271 core (ROUTE-REFRESH is RFC 2918).
    "bgp_routing": {
        "Message": E(marker="string", length="integer", type="integer"),
        "OpenMessage": E(version="integer", myAutonomousSystem="integer", holdTime="integer", bgpIdentifier="string", optionalParametersLength="integer"),
        "UpdateMessage": E(withdrawnRoutesLength="integer", totalPathAttributeLength="integer"),
        "NotificationMessage": E(errorCode="integer", errorSubcode="integer"),
        "PathAttribute": E(attributeFlags="integer", typeCode="integer", attributeLength="integer", origin="integer"),
        "KeepaliveMessage": E(headerOnly="boolean"),
    },
    # Faithful NTPv4 (RFC 5905) packet model — verified against the official RFC 5905.
    # stratum (0-255 range) + KissCode (extensible) -> not enforced as closed enums.
    "ntp_time": {
        "Packet": E(leapIndicator="integer", version="integer", mode="integer", stratum="integer", poll="integer", precision="integer", rootDelay="float", rootDispersion="float", referenceId="string", referenceTimestamp="datetime", originTimestamp="datetime", receiveTimestamp="datetime", transmitTimestamp="datetime"),
        "Header": E(leapIndicator="integer", version="integer", mode="integer", stratum="integer", poll="integer", precision="integer"),
        "KissCode": E(code="string", meaning="string"),
    },
    # Faithful MAVLink model — verified against the official mavlink XML message defs.
    # Only the stable/confirmed-complete enums enforced (MAV_STATE, MAV_MISSION_TYPE);
    # version-growing enums (MAV_TYPE/GPS_FIX_TYPE/MAV_FRAME) left as gaps.
    "mavlink_drones": {
        "Heartbeat": E(type="integer", autopilot="integer", baseMode="integer", customMode="integer", systemStatus="integer", mavlinkVersion="integer"),
        "SysStatus": E(load="integer", voltageBattery="integer", currentBattery="integer", batteryRemaining="integer", dropRateComm="integer", errorsComm="integer"),
        "GpsRawInt": E(timeUsec="integer", fixType="integer", lat="integer", lon="integer", alt="integer", vel="integer", satellitesVisible="integer"),
        "Attitude": E(timeBootMs="integer", roll="float", pitch="float", yaw="float", rollspeed="float", pitchspeed="float", yawspeed="float"),
        "GlobalPositionInt": E(timeBootMs="integer", lat="integer", lon="integer", alt="integer", relativeAlt="integer", vx="integer", vy="integer", vz="integer", hdg="integer"),
        "MissionItem": E(targetSystem="integer", targetComponent="integer", seq="integer", frame="integer", command="integer", current="integer", autocontinue="integer", x="float", y="float", z="float", missionType="integer"),
    },
    # px4_autopilot shares the verified MAVLink common.xml model (PX4 docs officially
    # state MAVLink is its protocol — normative-standard leverage, 3rd MAVLink-family member).
    "px4_autopilot": {
        "Heartbeat": E(type="integer", autopilot="integer", baseMode="integer", customMode="integer", systemStatus="integer", mavlinkVersion="integer"),
        "SysStatus": E(load="integer", voltageBattery="integer", currentBattery="integer", batteryRemaining="integer", dropRateComm="integer", errorsComm="integer"),
        "GpsRawInt": E(timeUsec="integer", fixType="integer", lat="integer", lon="integer", alt="integer", vel="integer", satellitesVisible="integer"),
        "Attitude": E(timeBootMs="integer", roll="float", pitch="float", yaw="float", rollspeed="float", pitchspeed="float", yawspeed="float"),
        "GlobalPositionInt": E(timeBootMs="integer", lat="integer", lon="integer", alt="integer", relativeAlt="integer", vx="integer", vy="integer", vz="integer", hdg="integer"),
        "MissionItem": E(targetSystem="integer", targetComponent="integer", seq="integer", frame="integer", command="integer", current="integer", autocontinue="integer", x="float", y="float", z="float", missionType="integer"),
    },
    # Faithful OpenXR model (official Khronos xr.xml registry, spec 1.1). Extension-free
    # core enums enforced: formFactor(2), sessionState(9), environmentBlendMode(3).
    # viewConfigurationType / referenceSpaceType have vendor-extension values -> gapped
    # (core-only enforcement would false-reject valid Varjo/MSFT values).
    "openxr": {
        "Instance": E(applicationName="string", applicationVersion="integer", engineName="string", engineVersion="integer", apiVersion="integer", enabledExtensionCount="integer"),
        "System": E(systemId="integer", formFactor="integer", systemName="string", vendorId="integer", maxSwapchainImageWidth="integer", maxSwapchainImageHeight="integer", orientationTracking="boolean", positionTracking="boolean"),
        "Session": E(systemId="integer", createFlags="integer", state="integer"),
        "ViewConfiguration": E(viewConfigurationType="integer", recommendedImageRectWidth="integer", recommendedImageRectHeight="integer", recommendedSwapchainSampleCount="integer", environmentBlendMode="integer"),
        "Swapchain": E(createFlags="integer", usageFlags="integer", format="integer", sampleCount="integer", width="integer", height="integer", faceCount="integer", arraySize="integer", mipCount="integer"),
    },
    # Faithful Apache Kafka model (official apache/kafka Java enums + protocol guide).
    # permissionType + isolationLevel stable since 2017 -> enforced. operation
    # (TWO_PHASE_COMMIT 2025) / groupState (KIP-848) / resourceType (USER added) are
    # version-growing; ApiKeys + error codes are large growing tables -> all gapped.
    "kafka": {
        "Topic": E(name="string", numPartitions="integer", replicationFactor="integer", isInternal="boolean", minInsyncReplicas="integer"),
        "Partition": E(topicName="string", partitionIndex="integer", leader="integer", replicas="string", isr="string"),
        "AclBinding": E(resourceType="string", resourceName="string", principal="string", host="string", operation="string", permissionType="string"),
        "ConsumerGroup": E(groupId="string", protocolType="string", state="string", generationId="integer"),
        "FetchRequest": E(topicName="string", partitionIndex="integer", fetchOffset="integer", maxBytes="integer", isolationLevel="string"),
    },
    # Faithful ONNX model (official onnx/onnx onnx.proto3, commit ef516e7b). attributeType
    # (15, stable since IR v8) + dataLocation (2) enforced. dataType is version-growing
    # (FP8 v9 / INT4 v10 / FP4 v11 / INT2 v13, ~yearly) -> gapped per MAVLink precedent.
    "onnx_runtime": {
        "ModelProto": E(irVersion="integer", producerName="string", producerVersion="string", domain="string", modelVersion="integer", docString="string"),
        "GraphProto": E(name="string", docString="string"),
        "NodeProto": E(name="string", opType="string", domain="string", docString="string"),
        "TensorProto": E(name="string", dataType="integer", dataLocation="integer", docString="string"),
        "AttributeProto": E(name="string", type="integer", docString="string"),
    },
    # Faithful ROS 2 navigation model (official ros2 .msg files, rolling branch).
    # GoalStatus.status / NavSatFix.status+positionCovarianceType / BatteryState
    # status+health enforced. service is a combinable BITMASK (not an enum) and
    # powerSupplyTechnology is version-growing (TERNARY/VRLA recent) -> both gapped.
    "ros2_nav": {
        "GoalStatus": E(goalId="string", stamp="datetime", status="integer"),
        "NavSatFix": E(latitude="float", longitude="float", altitude="float", status="integer", service="integer", positionCovarianceType="integer"),
        "BatteryState": E(voltage="float", temperature="float", current="float", charge="float", percentage="float", powerSupplyStatus="integer", powerSupplyHealth="integer", powerSupplyTechnology="integer", present="boolean"),
        "Odometry": E(childFrameId="string", poseX="float", poseY="float", poseZ="float", twistLinearX="float", twistLinearY="float", twistLinearZ="float", twistAngularX="float", twistAngularY="float", twistAngularZ="float"),
    },
    # mavlink_swarm shares the verified MAVLink common.xml model (same official spec as
    # mavlink_drones — normative-standard leverage, FHIR-family pattern). Same enum
    # discipline: MAV_STATE + MAV_MISSION_TYPE enforced; version-growing sets gapped.
    "mavlink_swarm": {
        "Heartbeat": E(type="integer", autopilot="integer", baseMode="integer", customMode="integer", systemStatus="integer", mavlinkVersion="integer"),
        "SysStatus": E(load="integer", voltageBattery="integer", currentBattery="integer", batteryRemaining="integer", dropRateComm="integer", errorsComm="integer"),
        "GpsRawInt": E(timeUsec="integer", fixType="integer", lat="integer", lon="integer", alt="integer", vel="integer", satellitesVisible="integer"),
        "Attitude": E(timeBootMs="integer", roll="float", pitch="float", yaw="float", rollspeed="float", pitchspeed="float", yawspeed="float"),
        "GlobalPositionInt": E(timeBootMs="integer", lat="integer", lon="integer", alt="integer", relativeAlt="integer", vx="integer", vy="integer", vz="integer", hdg="integer"),
        "MissionItem": E(targetSystem="integer", targetComponent="integer", seq="integer", frame="integer", command="integer", current="integer", autocontinue="integer", x="float", y="float", z="float", missionType="integer"),
    },
    # Faithful Modbus TCP model — verified against the Modbus Application Protocol spec
    # (public function/exception code tables). protocolId is always 0 for Modbus/TCP.
    "modbus_tcp": {
        "MbapHeader": E(transactionId="integer", protocolId="integer", length="integer", unitId="integer"),
        "Request": E(transactionId="integer", protocolId="integer", unitId="integer", functionCode="integer", startingAddress="integer", quantity="integer"),
        "Response": E(transactionId="integer", unitId="integer", functionCode="integer", byteCount="integer"),
        "ExceptionResponse": E(transactionId="integer", unitId="integer", exceptionFunctionCode="integer", exceptionCode="integer"),
    },
    # Faithful GS1 EPCIS 2.0 model — verified against the official GS1 EPCIS 2.0
    # standard (ref.gs1.org). bizStep/disposition are large CBV vocabs -> not enforced.
    "gs1_epcis": {
        "EPCISEvent": E(eventId="string", eventType="string", eventTime="datetime", recordTime="datetime", eventTimeZoneOffset="string", certificationInfo="string"),
        "ObjectEvent": E(eventId="string", action="string", bizStep="string", disposition="string", readPoint="string", bizLocation="string", eventTime="datetime", recordTime="datetime"),
        "AggregationEvent": E(eventId="string", parentID="string", action="string", bizStep="string", disposition="string", readPoint="string", eventTime="datetime"),
        "TransactionEvent": E(eventId="string", parentID="string", action="string", bizStep="string", eventTime="datetime"),
        "TransformationEvent": E(eventId="string", transformationID="string", bizStep="string", disposition="string", readPoint="string", eventTime="datetime"),
        "AssociationEvent": E(eventId="string", parentID="string", action="string", bizStep="string", eventTime="datetime"),
    },
    # Faithful ISO 8583 model — MTI-position enums from the public ISO 8583 reference
    # (the ISO standard itself is paywalled). transactionType/responseCode partial -> gapped.
    "iso_8583": {
        "Message": E(mti="string", messageClass="string", messageFunction="string", messageOrigin="string", version="string", stan="string", processingCode="string", transmissionDateTime="datetime"),
        "ProcessingCode": E(transactionType="string", accountTypeFrom="string", accountTypeTo="string"),
        "DataElement": E(fieldNumber="integer", name="string", dataType="string", length="integer", value="string"),
        "ResponseCode": E(code="string", meaning="string", requiresCardPickup="boolean"),
    },
    # Faithful The Graph (Studio + Network) model — verified against the official
    # graph-network-subgraph schema + Studio API. Subgraph.status is array -> dropped.
    "thegraph": {
        "Subgraph": E(id="integer", name="string", displayName="string", description="string", sourceCodeUrl="string", imageUrl="string", createdAt="datetime", updatedAt="datetime"),
        "SubgraphDeployment": E(id="string", ipfsHash="string", createdAt="integer", stakedTokens="integer", signalledTokens="integer", queryFeesAmount="integer", activeSubgraphCount="integer", transferredToL2="boolean"),
        "Indexer": E(id="string", createdAt="integer", stakedTokens="integer", allocatedTokens="integer", queryFeesCollected="integer", delegatedTokens="integer", isLegacy="boolean"),
        "Allocation": E(id="string", allocatedTokens="integer", createdAtEpoch="integer", closedAtEpoch="integer", queryFeesCollected="integer", status="string", isLegacy="boolean"),
        "PublishedSubgraph": E(id="string", networkCaip2Id="string", networkSubgraphId="string", createdAt="datetime", updatedAt="datetime"),
    },
    # Faithful Magento 2 / Adobe Commerce model — verified against the official
    # magento2 source (Sales/Catalog model constants). status/visibility are int-coded.
    "magento": {
        "Order": E(entityId="integer", incrementId="string", state="string", status="string", customerId="integer", customerEmail="string", grandTotal="float", subtotal="float", createdAt="datetime", updatedAt="datetime"),
        "Product": E(id="integer", sku="string", name="string", price="float", weight="float", status="integer", visibility="integer", typeId="string", attributeSetId="integer", createdAt="datetime"),
        "Customer": E(id="integer", email="string", firstname="string", lastname="string", groupId="integer", storeId="integer", websiteId="integer", createdAt="datetime"),
        "Category": E(id="integer", parentId="integer", name="string", isActive="boolean", position="integer", level="integer", path="string", productCount="integer"),
        "Invoice": E(entityId="integer", incrementId="string", orderId="integer", state="integer", grandTotal="float", subtotal="float", createdAt="datetime"),
        "Shipment": E(entityId="integer", incrementId="string", orderId="integer", storeId="integer", totalQty="float", totalWeight="float", createdAt="datetime"),
    },
    # Faithful Cloudinary Admin API model — verified against cloudinary.com/documentation.
    "cloudinary": {
        "Resource": E(assetId="string", publicId="string", resourceType="string", type="string", format="string", bytes="integer", width="integer", height="integer", version="integer", url="string", secureUrl="string", createdAt="datetime"),
        "Folder": E(name="string", path="string", externalId="string", createdAt="datetime", updatedAt="datetime"),
        "Transformation": E(name="string", named="boolean", used="boolean", allowedForStrict="boolean"),
        "UploadPreset": E(name="string", unsigned="boolean", externalId="string", live="boolean"),
        "Tag": E(name="string"),
    },
    # Faithful MEDITECH FHIR R4 model — ONC-certified EHR exposes HL7 FHIR R4 US Core;
    # normative R4 REQUIRED-binding value sets (hl7.org/fhir/R4).
    "meditech": {
        "Patient": E(id="string", resourceType="string", gender="string", birthDate="string", active="boolean", deceasedBoolean="boolean"),
        "Observation": E(id="string", resourceType="string", status="string", effectiveDateTime="datetime", valueString="string", issued="datetime"),
        "Encounter": E(id="string", resourceType="string", status="string", serviceType="string", period="string"),
        "MedicationRequest": E(id="string", resourceType="string", status="string", intent="string", authoredOn="datetime"),
        "AllergyIntolerance": E(id="string", resourceType="string", clinicalStatus="string", criticality="string", recordedDate="datetime"),
        "Condition": E(id="string", resourceType="string", clinicalStatus="string", recordedDate="datetime"),
    },
    # Faithful NextGen Healthcare FHIR R4 model — ONC-certified EHR exposes HL7 FHIR R4
    # US Core; normative R4 REQUIRED-binding value sets (hl7.org/fhir/R4).
    "nextgen": {
        "Patient": E(id="string", resourceType="string", gender="string", birthDate="string", active="boolean", deceasedBoolean="boolean"),
        "Observation": E(id="string", resourceType="string", status="string", effectiveDateTime="datetime", valueString="string", issued="datetime"),
        "Encounter": E(id="string", resourceType="string", status="string", serviceType="string", period="string"),
        "MedicationRequest": E(id="string", resourceType="string", status="string", intent="string", authoredOn="datetime"),
        "AllergyIntolerance": E(id="string", resourceType="string", clinicalStatus="string", criticality="string", recordedDate="datetime"),
        "Condition": E(id="string", resourceType="string", clinicalStatus="string", recordedDate="datetime"),
    },
    # Faithful Cerner/Oracle Health Ignite FHIR R4 model — Cerner Millennium exposes
    # HL7 FHIR R4; normative R4 REQUIRED-binding value sets (hl7.org/fhir/R4).
    "cerner_ignite": {
        "Patient": E(id="string", resourceType="string", gender="string", birthDate="string", active="boolean", deceasedBoolean="boolean"),
        "Observation": E(id="string", resourceType="string", status="string", effectiveDateTime="datetime", valueString="string", issued="datetime"),
        "Encounter": E(id="string", resourceType="string", status="string", serviceType="string", period="string"),
        "MedicationRequest": E(id="string", resourceType="string", status="string", intent="string", authoredOn="datetime"),
        "AllergyIntolerance": E(id="string", resourceType="string", clinicalStatus="string", criticality="string", recordedDate="datetime"),
        "Condition": E(id="string", resourceType="string", clinicalStatus="string", recordedDate="datetime"),
    },
    # Faithful Allscripts/Veradigm FHIR R4 model — exposes HL7 FHIR R4; normative
    # R4 REQUIRED-binding value sets (hl7.org/fhir/R4).
    "allscripts": {
        "Patient": E(id="string", resourceType="string", gender="string", birthDate="string", active="boolean", deceasedBoolean="boolean"),
        "Observation": E(id="string", resourceType="string", status="string", effectiveDateTime="datetime", valueString="string", issued="datetime"),
        "Encounter": E(id="string", resourceType="string", status="string", serviceType="string", period="string"),
        "MedicationRequest": E(id="string", resourceType="string", status="string", intent="string", authoredOn="datetime"),
        "AllergyIntolerance": E(id="string", resourceType="string", clinicalStatus="string", criticality="string", recordedDate="datetime"),
        "Condition": E(id="string", resourceType="string", clinicalStatus="string", recordedDate="datetime"),
    },
    # Faithful Epic on FHIR R4 model — Epic's FHIR endpoint implements HL7 FHIR R4;
    # status fields use the normative R4 REQUIRED-binding value sets (hl7.org/fhir/R4).
    "epic_fhir": {
        "Patient": E(id="string", resourceType="string", gender="string", birthDate="string", active="boolean", deceasedBoolean="boolean"),
        "Observation": E(id="string", resourceType="string", status="string", effectiveDateTime="datetime", valueString="string", issued="datetime"),
        "Encounter": E(id="string", resourceType="string", status="string", serviceType="string", period="string"),
        "MedicationRequest": E(id="string", resourceType="string", status="string", intent="string", authoredOn="datetime"),
        "AllergyIntolerance": E(id="string", resourceType="string", clinicalStatus="string", criticality="string", recordedDate="datetime"),
        "Condition": E(id="string", resourceType="string", clinicalStatus="string", recordedDate="datetime"),
    },
    # Faithful SMART on FHIR R4 model — SMART apps consume HL7 FHIR R4; same normative
    # R4 REQUIRED-binding value sets (hl7.org/fhir/R4).
    "smart_on_fhir": {
        "Patient": E(id="string", resourceType="string", gender="string", birthDate="string", active="boolean", deceasedBoolean="boolean"),
        "Observation": E(id="string", resourceType="string", status="string", effectiveDateTime="datetime", valueString="string", issued="datetime"),
        "Encounter": E(id="string", resourceType="string", status="string", serviceType="string", period="string"),
        "MedicationRequest": E(id="string", resourceType="string", status="string", intent="string", authoredOn="datetime"),
        "AllergyIntolerance": E(id="string", resourceType="string", clinicalStatus="string", criticality="string", recordedDate="datetime"),
        "Condition": E(id="string", resourceType="string", clinicalStatus="string", recordedDate="datetime"),
    },
    # Faithful Pinecone API model — verified against the official pinecone-io OpenAPI.
    "pinecone": {
        "Index": E(name="string", dimension="integer", metric="string", host="string", state="string", deletionProtection="string", vectorType="string", cloud="string", ready="boolean"),
        "Collection": E(name="string", dimension="integer", status="string", vectorCount="integer", size="integer", environment="string"),
        "Vector": E(id="string", namespace="string"),
        "Namespace": E(name="string", recordCount="integer"),
    },
    # Faithful Deel API model — verified against developer.deel.com OpenAPI. Contract
    # .status partial + Adjustment variant-specific + Milestone inferred -> not enforced.
    "deel": {
        "Contract": E(id="string", contractId="string", type="string", status="string", teamId="string", country="string", currency="string", externalId="string"),
        "Worker": E(profileId="string", name="string", firstName="string", lastName="string", email="string", country="string"),
        "Milestone": E(id="string", title="string", amount="float", status="string", contractId="string", createdAt="datetime"),
        "Timesheet": E(id="string", contractId="string", date="datetime", hours="float", description="string", status="string", reporterId="string"),
        "Payment": E(paymentId="string", dateFrom="datetime", dateTo="datetime", status="string", currency="string", entityType="string"),
    },
    # Faithful GBFS (General Bikeshare Feed Spec) model — verified against the
    # official MobilityData/gbfs spec. rentalMethods is array-valued -> not enforced.
    "gbfs": {
        "SystemInformation": E(systemId="string", name="string", operator="string", url="string", timezone="string", openingHours="string", phoneNumber="string", email="string", feedContactEmail="string"),
        "VehicleType": E(vehicleTypeId="string", formFactor="string", propulsionType="string", returnConstraint="string", maxRangeMeters="float", riderCapacity="integer", wheelCount="integer", maxPermittedSpeed="integer", minAge="integer"),
        "Station": E(stationId="string", name="string", lat="float", lon="float", address="string", city="string", regionId="string", capacity="integer", isVirtualStation="boolean", isChargingStation="boolean", parkingType="string"),
        "StationStatus": E(stationId="string", numVehiclesAvailable="integer", numDocksAvailable="integer", isInstalled="boolean", isRenting="boolean", isReturning="boolean", lastReported="datetime"),
        "Vehicle": E(vehicleId="string", lat="float", lon="float", isReserved="boolean", isDisabled="boolean", vehicleTypeId="string", currentRangeMeters="float", lastReported="datetime"),
        "Region": E(regionId="string", name="string"),
    },
    # Faithful Mambu API v2 model — verified against the official Mambu OpenAPI
    # (api.mambu.com / demo.mambu.com openapi resources).
    "mambu": {
        "LoanAccount": E(id="string", encodedKey="string", accountState="string", accountSubState="string", accountHolderType="string", accountHolderKey="string", loanAmount="float", loanName="string", daysInArrears="integer", creationDate="datetime", approvedDate="datetime", closedDate="datetime"),
        "DepositAccount": E(id="string", encodedKey="string", accountState="string", accountHolderType="string", accountHolderKey="string", creationDate="datetime", approvedDate="datetime"),
        "Client": E(id="string", encodedKey="string", state="string", firstName="string", lastName="string", emailAddress="string", mobilePhone="string", creationDate="datetime"),
        "Group": E(id="string", encodedKey="string", groupName="string", assignedBranchKey="string", creationDate="datetime"),
        "LoanTransaction": E(id="string", encodedKey="string", type="string", amount="float", notes="string", creationDate="datetime", bookingDate="datetime", valueDate="datetime"),
    },
    # Faithful Patreon API v2 model — verified against docs.patreon.com.
    # amounts integer cents; null enum members handled by the falsy guard.
    "patreon": {
        "User": E(id="string", about="string", fullName="string", firstName="string", lastName="string", email="string", isCreator="boolean", isEmailVerified="boolean", likeCount="integer", created="datetime"),
        "Member": E(id="string", patronStatus="string", lastChargeStatus="string", fullName="string", email="string", currentlyEntitledAmountCents="integer", campaignLifetimeSupportCents="integer", willPayAmountCents="integer", isFollower="boolean", isFreeTrial="boolean", lastChargeDate="datetime", nextChargeDate="datetime", pledgeRelationshipStart="datetime"),
        "Campaign": E(id="string", creationName="string", currency="string", name="string", patronCount="integer", payPerName="string", isMonthly="boolean", isNsfw="boolean", createdAt="datetime", publishedAt="datetime"),
        "Tier": E(id="string", amountCents="integer", description="string", patronCount="integer", published="boolean", requiresShipping="boolean", title="string", createdAt="datetime"),
        "Benefit": E(id="string", benefitType="string", description="string", isDeleted="boolean", isPublished="boolean", title="string", tiersCount="integer", createdAt="datetime"),
    },
    # Faithful commercetools Composable Commerce API model — verified against
    # docs.commercetools.com + commercetools-api-reference. Money objects dropped.
    "commercetools": {
        "Order": E(id="string", version="integer", orderNumber="string", customerId="string", customerEmail="string", orderState="string", paymentState="string", shipmentState="string", createdAt="datetime", lastModifiedAt="datetime"),
        "Cart": E(id="string", version="integer", customerId="string", cartState="string", createdAt="datetime", lastModifiedAt="datetime"),
        "Payment": E(id="string", version="integer", key="string", customerId="string", createdAt="datetime", lastModifiedAt="datetime"),
        "Product": E(id="string", version="integer", key="string", priceMode="string", createdAt="datetime", lastModifiedAt="datetime"),
        "Customer": E(id="string", version="integer", key="string", email="string", firstName="string", lastName="string", isEmailVerified="boolean", createdAt="datetime"),
        "Transaction": E(id="string", timestamp="datetime", type="string", state="string", interactionId="string"),
    },
    # Faithful Sendbird Chat Platform API model — verified against sendbird.com/docs.
    # Channels partially confirmed (some endpoints 404); timestamps Unix int ms.
    "sendbird": {
        "User": E(userId="string", nickname="string", profileUrl="string", accessToken="string", isActive="boolean", role="string", createdAt="integer", lastSeenAt="integer", isOnline="boolean"),
        "Message": E(messageId="integer", type="string", customType="string", message="string", channelUrl="string", createdAt="integer", updatedAt="integer", isRemoved="boolean"),
        "GroupChannel": E(channelUrl="string", name="string", memberCount="integer", isDistinct="boolean", createdAt="integer"),
        "OpenChannel": E(channelUrl="string", name="string", participantCount="integer", createdAt="integer"),
    },
    # Faithful OpenSea API v2 model — verified against @opensea/api-types + docs.
    # nested price/asset/criteria objects dropped. Listing.type inferred -> not enforced.
    "opensea": {
        "Nft": E(identifier="string", collection="string", contract="string", tokenStandard="string", name="string", description="string", imageUrl="string", openseaUrl="string", isDisabled="boolean", isNsfw="boolean", updatedAt="datetime"),
        "Collection": E(collection="string", name="string", description="string", imageUrl="string", safelistStatus="string", isDisabled="boolean", isNsfw="boolean", totalSupply="integer", createdDate="datetime"),
        "Listing": E(orderHash="string", chain="string", protocolAddress="string", remainingQuantity="integer", orderCreatedAt="integer", type="string", status="string"),
        "Offer": E(orderHash="string", chain="string", protocolAddress="string", remainingQuantity="integer", orderCreatedAt="integer", status="string"),
        "Account": E(address="string", username="string", bio="string", website="string", joinedDate="datetime"),
    }
,
    # Faithful Docker Engine API model — verified against the official moby/moby
    # swagger.yaml. Network scope/driver are open (plugins) -> not enforced.
    "docker": {
        "Container": E(id="string", image="string", imageID="string", command="string", state="string", created="integer", sizeRw="integer"),
        "Image": E(id="string", parent="string", comment="string", container="string", size="integer", created="string"),
        "Network": E(id="string", name="string", scope="string", driver="string", enableIPv6="boolean", internal="boolean", attachable="boolean", created="string"),
        "Volume": E(name="string", driver="string", mountpoint="string", scope="string", createdAt="string"),
    },
    # Faithful Kubernetes API model — verified against the official k8s OpenAPI.
    "kubernetes": {
        "Pod": E(name="string", namespace="string", phase="string", nodeName="string", podIP="string", qosClass="string", restartPolicy="string"),
        "Service": E(name="string", namespace="string", type="string", clusterIP="string", externalName="string"),
        "Deployment": E(name="string", namespace="string", replicas="integer", readyReplicas="integer", updatedReplicas="integer", observedGeneration="integer"),
        "Namespace": E(name="string", phase="string", deletionTimestamp="datetime"),
        "Node": E(name="string", address="string", addressType="string"),
        "PersistentVolume": E(name="string", phase="string", message="string"),
    },
    # Faithful LINE Messaging API model — verified against github.com/line/line-openapi.
    "line_api": {
        "Message": E(type="string", text="string", originalContentUrl="string", previewImageUrl="string", duration="integer"),
        "Source": E(type="string", userId="string", groupId="string", roomId="string"),
        "Event": E(type="string", mode="string", replyToken="string", timestamp="integer", webhookEventId="string"),
        "Profile": E(displayName="string", userId="string", pictureUrl="string", statusMessage="string", language="string"),
        "SentMessage": E(id="string", quoteToken="string"),
        "NarrowcastProgress": E(phase="string", successCount="integer", failureCount="integer", targetCount="integer"),
    },
    # Faithful Telegram Bot API model — verified against core.telegram.org/bots/api.
    # timestamps Unix integer; nested object refs dropped.
    "telegram_api": {
        "User": E(id="integer", isBot="boolean", firstName="string", lastName="string", username="string", languageCode="string", isPremium="boolean"),
        "Chat": E(id="integer", type="string", title="string", username="string", firstName="string", lastName="string", isForum="boolean"),
        "Message": E(messageId="integer", date="integer", text="string", chatId="integer"),
        "ChatMember": E(status="string", isAnonymous="boolean", customTitle="string"),
    },
    # Faithful Kong Gateway Admin API model — verified against the official Kong
    # entity schemas (github.com/Kong/kong db/schema/entities). timestamps Unix int.
    "kong": {
        "Service": E(id="string", name="string", protocol="string", host="string", port="integer", path="string", retries="integer", enabled="boolean", connectTimeout="integer", createdAt="integer", updatedAt="integer"),
        "Route": E(id="string", name="string", service="string", stripPath="boolean", preserveHost="boolean", priority="integer", pathHandling="string", httpsRedirectStatusCode="integer", createdAt="integer"),
        "Consumer": E(id="string", username="string", customId="string", createdAt="integer", updatedAt="integer"),
        "Plugin": E(id="string", name="string", instanceName="string", service="string", route="string", consumer="string", enabled="boolean", createdAt="integer"),
        "Upstream": E(id="string", name="string", algorithm="string", hashOn="string", hashFallback="string", hashOnHeader="string", createdAt="integer"),
        "Target": E(id="string", upstream="string", target="string", weight="integer", createdAt="integer"),
    },
    # Faithful World Bank Indicators API model — verified against the live
    # api.worldbank.org/v2 endpoints (code lists are documented closed sets).
    "worldbank": {
        "Country": E(id="string", iso2Code="string", name="string", capitalCity="string", incomeLevelId="string", lendingTypeId="string", regionId="string", longitude="string", latitude="string"),
        "Indicator": E(id="string", name="string", unit="string", sourceId="string", sourceNote="string", sourceOrganization="string"),
        "Source": E(id="string", name="string", code="string", lastUpdated="string", dataAvailability="boolean", concepts="integer"),
        "IncomeLevel": E(id="string", name="string"),
        "LendingType": E(id="string", name="string"),
        "Topic": E(id="string", name="string"),
    },
    # Faithful HL7 FHIR R4 model — verified against the official HL7 FHIR R4 spec
    # (hl7.org/fhir/R4). Status fields use the REQUIRED-binding closed value sets.
    "hl7_fhir": {
        "Patient": E(id="string", resourceType="string", gender="string", birthDate="string", active="boolean", deceasedBoolean="boolean"),
        "Observation": E(id="string", resourceType="string", status="string", effectiveDateTime="datetime", valueString="string", issued="datetime"),
        "Encounter": E(id="string", resourceType="string", status="string", serviceType="string", period="string"),
        "MedicationRequest": E(id="string", resourceType="string", status="string", intent="string", authoredOn="datetime"),
        "AllergyIntolerance": E(id="string", resourceType="string", clinicalStatus="string", criticality="string", recordedDate="datetime"),
        "Condition": E(id="string", resourceType="string", clinicalStatus="string", recordedDate="datetime"),
    },
    # Faithful ChEMBL Web Services model — verified against the EBI ChEMBL API.
    "chembl": {
        "Molecule": E(chemblId="string", prefName="string", moleculeType="string", blackBoxWarning="integer", therapeuticFlag="boolean", firstApproval="integer"),
        "Assay": E(chemblId="string", assayType="string", description="string", confidenceScore="integer", targetChemblId="string", documentChemblId="string"),
        "Target": E(chemblId="string", prefName="string", targetType="string", organism="string", speciesGroupFlag="boolean"),
        "Activity": E(activityId="integer", moleculeChemblId="string", assayChemblId="string", standardValue="string", standardType="string", documentYear="integer"),
        "Document": E(chemblId="string", title="string", docType="string", year="integer", pubmedId="integer", doi="string"),
    },
    # Faithful Discord model — verified against the official discord-api-docs
    # (Channel Types table, etc.). Channel.type is the documented int-coded enum.
    "discord": {
        "Channel": E(id="string", type="integer", name="string", guildId="string", position="integer", topic="string", nsfw="boolean"),
        "Guild": E(id="string", name="string", ownerId="string", description="string", premiumTier="integer", verificationLevel="integer"),
        "Message": E(id="string", channelId="string", content="string", type="integer", pinned="boolean", tts="boolean", timestamp="datetime"),
        "User": E(id="string", username="string", discriminator="string", globalName="string", bot="boolean"),
        "Role": E(id="string", name="string", color="integer", position="integer", hoist="boolean", managed="boolean", mentionable="boolean"),
    },
    # Faithful Monzo model — verified against official docs.monzo.com.
    # amounts integer minor units (pennies).
    "monzo": {
        "Account": E(id="string", description="string", type="string", created="datetime"),
        "Balance": E(balance="integer", totalBalance="integer", currency="string", spendToday="integer"),
        "Transaction": E(id="string", amount="integer", currency="string", description="string", category="string", declineReason="string", isLoad="boolean", merchant="string", created="datetime", settled="datetime"),
        "Pot": E(id="string", name="string", balance="integer", currency="string", deleted="boolean", created="datetime", updated="datetime"),
        "Attachment": E(id="string", userId="string", externalId="string", fileUrl="string", fileType="string", created="datetime"),
    },
    # Faithful Ramp model — verified against the official Ramp Developer API OpenAPI
    # (docs.ramp.com/openapi/developer-api.json). snake_case->camelCase.
    "ramp": {
        "Card": E(id="string", state="string", lastFour="string", cardholderName="string", cardholderID="string", isPhysical="boolean", createdAt="datetime"),
        "Transaction": E(id="string", state="string", amount="float", currencyCode="string", cardID="string", merchantName="string", userTransactionTime="datetime", settlementDate="datetime"),
        "User": E(id="string", email="string", firstName="string", lastName="string", role="string", status="string", departmentID="string", isManager="boolean"),
        "Department": E(id="string", name="string"),
        "Reimbursement": E(id="string", state="string", amount="float", currency="string", type="string", userID="string", direction="string", createdAt="datetime"),
        "Bill": E(id="string", status="string", amount="integer", currencyCode="string", invoiceNumber="string", statusSummary="string", createdAt="datetime", dueAt="datetime"),
    },
    # Faithful AfterShip Tracking model — verified against the official AfterShip SDK
    # (github.com/AfterShip/aftership-sdk-nodejs). snake_case->camelCase.
    "aftership": {
        "Tracking": E(id="string", trackingNumber="string", slug="string", tag="string", subtag="string", deliveryType="string", active="boolean", expectedDelivery="string", orderId="string", createdAt="datetime", updatedAt="datetime"),
        "Checkpoint": E(checkpointTime="datetime", slug="string", tag="string", subtag="string", message="string", location="string", city="string", countryIso3="string"),
        "Courier": E(slug="string", name="string", phone="string", webUrl="string", defaultLanguage="string"),
        "Notification": E(emails="string", smses="string"),
        "EstimatedDeliveryDate": E(estimatedDeliveryDate="string", confidenceScore="float", estimatedDeliveryDateMin="string", estimatedDeliveryDateMax="string"),
    },
    # Faithful Square model (replaces the generic Stripe-shaped payments model)
    # so the actor can be doc-verified to L5 (ADR 260607 §8).
    "square": {
        "Payment": E(orderId="string", customerId="string", amount="integer", currency="string", status="string", sourceType="string"),
        "Order": E(locationId="string", customerId="string", state="string", totalAmount="integer", currency="string"),
        "Customer": E(givenName="string", familyName="string", emailAddress="string", phoneNumber="string"),
        "Refund": E(paymentId="string", amount="integer", currency="string", status="string", reason="string"),
        "CatalogObject": E(type="string", name="string", version="integer"),
        "Invoice": E(orderId="string", status="string", invoiceNumber="string"),
    },
    # Faithful Autoware AD API model (official autoware_adapi_v1_msgs .msg files,
    # autowarefoundation/autoware_adapi_msgs main). All five state enums enforced:
    # each .msg has a single commit since introduction (2022/2023) in an explicitly
    # versioned v1 API — stable-since-introduction + version-anchored closedness.
    "autoware": {
        "OperationModeState": E(stamp="datetime", mode="integer", isAutowareControlEnabled="boolean", isInTransition="boolean", isStopModeAvailable="boolean", isAutonomousModeAvailable="boolean", isLocalModeAvailable="boolean", isRemoteModeAvailable="boolean"),
        "RouteState": E(stamp="datetime", state="integer"),
        "LocalizationInitializationState": E(stamp="datetime", state="integer"),
        "MotionState": E(stamp="datetime", state="integer"),
        "Gear": E(status="integer"),
    },
    # Faithful Baidu Apollo model (official ApolloAuto/apollo modules/common_msgs
    # proto3 files, master). drivingMode/frontBumperEvent/rightOfWayStatus/
    # fusionStatus enforced (semantically complete small sets, incl. Apollo's own
    # WARNNING spelling). errorCode/gearLocation/type/subType/trajectoryType are
    # version-growing and gnssStatus/lidarStatus deprecated -> all gapped.
    "apollo_auto": {
        "Chassis": E(engineStarted="boolean", speedMps="float", throttlePercentage="float", brakePercentage="float", steeringPercentage="float", parkingBrake="boolean", wiper="boolean", drivingMode="string", errorCode="string", gearLocation="string", frontBumperEvent="string"),
        "PerceptionObstacle": E(theta="float", length="float", width="float", height="float", trackingTime="float", timestamp="float", confidence="float", type="string", subType="string"),
        "ADCTrajectory": E(totalPathLength="float", totalPathTime="float", isReplan="boolean", replanReason="string", carInDeadEnd="boolean", isCollision="boolean", rightOfWayStatus="string", trajectoryType="string"),
        "LocalizationStatus": E(measurementTime="float", stateMessage="string", fusionStatus="string", gnssStatus="string", lidarStatus="string"),
    },
    # Faithful IBM Qiskit model (official Qiskit/qiskit jobstatus.py + Qiskit/
    # qiskit-ibm-runtime runtime_job_v2.py / base_runtime_job.py / ibm_backend.py).
    # Job.status (JobStatus enum, stable since 2017) + RuntimeJob.status (typed
    # closed Literal in runtime_job_v2) enforced.
    "ibm_qiskit": {
        "Job": E(jobId="string", backend="string", status="string"),
        "RuntimeJob": E(jobId="string", programId="string", creationDate="datetime", image="string", sessionId="string", version="integer", private="boolean", status="string"),
        "Backend": E(name="string", backendVersion="string", numQubits="integer", simulator="boolean", local="boolean", conditional="boolean", openPulse="boolean", memory="boolean", dt="float", dtm="float"),
    },
    # Faithful freee accounting model (official freee/freee-api-schema OpenAPI,
    # v2020_06_15/open-api-3/api-schema.json) — replaces the generic CRM shape.
    # 10 enums enforced from the spec's own enum arrays; the claimed
    # AccountItem.searchable enum was REFUTED against the spec -> gapped.
    "freee": {
        "Deal": E(companyId="integer", issueDate="datetime", dueDate="datetime", amount="integer", dueAmount="integer", type="string", partnerId="integer", partnerCode="string", refNumber="string", status="string"),
        "AccountItem": E(name="string", companyId="integer", taxCode="integer", accountCategory="string", available="boolean", walletableId="integer", searchable="integer"),
        "Partner": E(name="string", code="string", companyId="integer", available="boolean", orgCode="integer", transferFeeHandlingSide="string"),
        "Invoice": E(invoiceNumber="string", issueDate="datetime", totalAmount="integer", invoiceStatus="string", paymentType="string"),
        "Company": E(displayName="string", role="string", orgCode="integer"),
        "Walletable": E(name="string", bankId="integer", type="string", syncStatus="string"),
    },
    # Faithful comma.ai openpilot model (official commaai/opendbc opendbc/car/car.capnp
    # + commaai/openpilot cereal/log.capnp, master). gearShifter enforced: the 10-value
    # set is byte-identical at openpilot v0.9.7 (2024) and master (2026) — two-year
    # stability across an otherwise actively-churning file. Cap'n Proto enums grow by
    # appending, so no other enum is enforced.
    "comma_ai_openpilot": {
        "Event": E(logMonoTime="integer", valid="boolean", logMessage="string"),
        "CarState": E(vEgo="float", aEgo="float", standstill="boolean", gasPressed="boolean", brakePressed="boolean", steeringAngleDeg="float", steeringTorque="float", gearShifter="string", leftBlinker="boolean", rightBlinker="boolean"),
        "CarControl": E(enabled="boolean", latActive="boolean", longActive="boolean", leftBlinker="boolean", rightBlinker="boolean"),
        "CarParams": E(brand="string", carFingerprint="string", minEnableSpeed="float", minSteerSpeed="float", mass="float", wheelbase="float"),
    },
    # Faithful dbt artifact model (official schemas.getdbt.com versioned JSON Schemas:
    # manifest v12 + run-results v6 — immutable once published; a breaking change forces
    # vN+1, the cleanest closed-at-version anchor in the corpus). resourceType (19 @v12)
    # + RunResult.status (the exact 9-value anyOf union @v6) enforced.
    "dbt": {
        "Node": E(database="string", schema="string", name="string", packageName="string", uniqueId="string", alias="string", description="string", compiled="boolean", rawCode="string", resourceType="string"),
        "Source": E(database="string", schema="string", name="string", sourceName="string", sourceDescription="string", loader="string", identifier="string", uniqueId="string", resourceType="string"),
        "RunResult": E(threadId="string", executionTime="float", message="string", failures="integer", uniqueId="string", compiled="boolean", compiledCode="string", status="string"),
    },
    # Faithful Aave V3 model (official aave-dao/aave-v3-origin DataTypes.sol, main =
    # v3.4). interestRateMode enforced: {NONE, __DEPRECATED, VARIABLE} — stable-rate
    # retired in 3.2, positions preserved, closed at the fetched version. Bitmask
    # fields (configuration/collateralBitmap/borrowableBitmap/ltvzeroBitmap/data)
    # are combinable bit-fields, not enums -> gapped per corpus discipline.
    "aave": {
        "ReserveData": E(liquidityIndex="integer", currentLiquidityRate="integer", variableBorrowIndex="integer", currentVariableBorrowRate="integer", deficit="integer", lastUpdateTimestamp="integer", liquidationGracePeriodUntil="integer", aTokenAddress="string", variableDebtTokenAddress="string", accruedToTreasury="integer", virtualUnderlyingBalance="integer"),
        "EModeCategory": E(ltv="integer", liquidationThreshold="integer", liquidationBonus="integer", collateralBitmap="integer", isolated="boolean", label="string", borrowableBitmap="integer", ltvzeroBitmap="integer"),
        "UserConfigurationMap": E(data="integer"),
        "ExecuteBorrowParams": E(asset="string", user="string", onBehalfOf="string", interestRateStrategyAddress="string", amount="integer", interestRateMode="string", referralCode="integer", releaseUnderlying="boolean", oracle="string", userEModeCategory="integer"),
    },
    # Faithful Hugging Face Hub model (official huggingface/huggingface_hub hf_api.py
    # dataclasses, main). gated (typed Literal["auto","manual",False] — mixed-type,
    # kept faithfully) enforced on ModelInfo/DatasetInfo/SpaceInfo + ModelInfo.inference
    # (Literal["warm"]). pipelineTag is the open ML-task registry -> gapped; SpaceInfo
    # hardware/title/description/emoji were gemini-draft fabrications (live on
    # SpaceRuntime/SpaceCardData, not SpaceInfo) -> refuted and dropped.
    "huggingface": {
        "ModelInfo": E(author="string", downloads="integer", likes="integer", private="boolean", gated="string", pipelineTag="string", libraryName="string", sha="string", inference="string"),
        "DatasetInfo": E(author="string", downloads="integer", likes="integer", private="boolean", gated="string", sha="string", description="string", mainSize="integer", citation="string"),
        "SpaceInfo": E(author="string", sha="string", private="boolean", sdk="string", likes="integer", host="string", subdomain="string", gated="string"),
        "TransformersInfo": E(autoModel="string", customClass="string", pipelineTag="string", processor="string"),
    },
    # Faithful DJI Onboard SDK model (official dji-sdk/Onboard-SDK headers — repo
    # dormant since 2024-02 / OSDK discontinued by DJI, freezing its enums).
    # flight (3, incl. DJI's literal STOPED spelling) + gear (LandingGearMode, 9)
    # enforced as integers per telemetry encoding. DisplayMode (30 of 44 members
    # are MODE_RESERVED_n placeholders) gapped as reserved-slot-bearing; error
    # codes extension-bearing -> gapped. GPSDetail keeps DJI's verbatim member
    # casing (usedGPS/usedGLN/NSV/GPScounter).
    "dji_onboard_sdk": {
        "Status": E(flight="integer", mode="integer", gear="integer", error="integer"),
        "Battery": E(capacity="integer", voltage="integer", current="integer", percentage="integer"),
        "GlobalPosition": E(latitude="float", longitude="float", altitude="float", height="float", health="integer"),
        "GPSDetail": E(hdop="float", pdop="float", fix="float", gnssStatus="float", hacc="float", sacc="float", usedGPS="integer", usedGLN="integer", NSV="integer", GPScounter="integer"),
        "FlightAnomaly": E(impactInAir="boolean", randomFly="boolean", heightCtrlFail="boolean", rollPitchCtrlFail="boolean", yawCtrlFail="boolean", aircraftIsFalling="boolean", strongWindLevel1="boolean", strongWindLevel2="boolean", compassInstallationError="boolean", imuInstallationError="boolean"),
    },
    # Faithful Helium model (official helium/proto protobufs — the L1 chain
    # migrated to Solana in 2023, freezing these protos). LoRa PHY parameter enums
    # (Spreading/Bandwidth/Coderate/RegionSpreading) are physics-anchored closed
    # sets; packet.type + poc origin are tiny frozen sets. region + token_type
    # grew historically -> gapped.
    "helium": {
        "Packet": E(oui="integer", payload="string", timestamp="integer", signalStrength="float", frequency="float", datarate="string", snr="float", type="string"),
        "BlockchainPocReceiptV1": E(gateway="string", timestamp="integer", signal="integer", data="string", origin="string", signature="string", snr="float", frequency="float", channel="integer", datarate="string", addrHash="string", txPower="integer", rewardShares="integer"),
        "RadioTxReq": E(freq="integer", power="integer", invertPolarity="boolean", omitCrc="boolean", implicitHeader="boolean", payload="string", radio="string", bandwidth="string", spreading="string", coderate="string"),
        "TaggedSpreading": E(regionSpreading="string", maxPacketSize="integer"),
        "BlockchainBlockV1": E(prevHash="string", height="integer", time="integer", hbbftRound="integer", electionEpoch="integer", epochStart="integer", rescueSignature="string", bbaCompletion="string", snapshotHash="string"),
        "Payment": E(payee="string", amount="integer", memo="integer", max="boolean", tokenType="string"),
    },
    # Faithful LangChain core message model (official langchain-ai/langchain
    # libs/core typed sources). Per-class type Literals ('ai'/'tool'/'tool_call')
    # + ToolMessage.status Literal['success','error'] enforced; BaseMessage.type
    # is per-subclass (extension-bearing) and LogEntry.type is the open run-type
    # registry -> both gapped.
    "langchain": {
        "BaseMessage": E(content="string", additionalKwargs="string", responseMetadata="string", type="string", name="string"),
        "AIMessage": E(content="string", type="string", name="string", toolCalls="string", invalidToolCalls="string", usageMetadata="string"),
        "ToolMessage": E(content="string", type="string", name="string", toolCallId="string", artifact="string", status="string"),
        "ToolCall": E(name="string", args="string", type="string"),
        "UsageMetadata": E(inputTokens="integer", outputTokens="integer", totalTokens="integer", inputTokenDetails="string", outputTokenDetails="string"),
        "LogEntry": E(name="string", type="string", tags="string", metadata="string", startTime="datetime", streamedOutputStr="string", streamedOutput="string", inputs="string", finalOutput="string", endTime="datetime"),
    },
    # Faithful Blender bpy model (official version-PINNED API reference,
    # docs.blender.org/api/4.2). upAxis enforced (enum in ['X','Y','Z'] — the 3D
    # axis set cannot grow). Object.type version-growing (17 @4.2; the 4.2 page
    # itself carries the GPENCIL->GREASEPENCIL transition) and blendMethod
    # deprecated upstream @4.2 -> both gapped. location flattened to X/Y/Z
    # scalars per the ros2_nav Odometry precedent.
    "blender": {
        "Object": E(name="string", type="string", parent="string", upAxis="string", locationX="float", locationY="float", locationZ="float"),
        "Scene": E(name="string", frameStart="integer", frameEnd="integer", frameCurrent="integer", frameStep="integer"),
        "Material": E(name="string", useNodes="boolean", metallic="float", roughness="float", blendMethod="string"),
    },
    # Faithful Amazon Braket model (official amazon-braket-schemas-python pydantic
    # sources). executionDay enforced: 10-member calendar-anchored set (7 days + 3
    # aggregates; days of the week cannot grow) — incl. AWS's own singular
    # WEEKENDS="Weekend" value string. TaskMetadata.status is an untyped constr
    # upstream -> gapped. shotsRange tuple flattened per ros2_nav precedent.
    "aws_braket": {
        "ExecutionWindow": E(executionDay="string", windowStartHour="string", windowEndHour="string"),
        "DeviceServiceProperties": E(deviceLocation="string", updatedAt="datetime", getTaskPollIntervalMillis="integer", shotsRangeMin="integer", shotsRangeMax="integer"),
        "TaskMetadata": E(shots="integer", deviceId="string", createdAt="datetime", endedAt="datetime", status="string"),
    },
    # Faithful Google Quantum Engine model (official quantumlib/Cirq
    # quantum_v1alpha1 proto types — the versioned wire format of the Google
    # Quantum Engine API). State(7)/Health(5)/TimeSlotType(5) enforced at the
    # v1alpha1 anchor; Failure.Code (14, an error-code table) gapped per the
    # kafka/DJI error-table precedent.
    "google_cirq": {
        "QuantumJob": E(name="string", createTime="datetime", updateTime="datetime", labelFingerprint="string", description="string"),
        "ExecutionStatus": E(state="string", processorName="string", calibrationName="string"),
        "QuantumProcessor": E(name="string", health="string", expectedDownTime="datetime", expectedRecoveryTime="datetime"),
        "QuantumProgram": E(name="string", createTime="datetime", updateTime="datetime", labelFingerprint="string", description="string"),
        "QuantumTimeSlot": E(processorName="string", startTime="datetime", endTime="datetime", timeSlotType="string"),
    },
    # Faithful D-Wave SAPI model (official dwavesystems/dwave-cloud-client
    # pydantic models + constants). ProblemStatus enforced: the upstream
    # docstring spells out the COMPLETE state machine incl. terminal states.
    # ProblemType (ising->qubo->bqm/cqm/dqm/nl growth) + encoding formats
    # (BQ deprecated-for-submission) -> gapped.
    "d_wave": {
        "ProblemMetadata": E(type="string", label="string", status="string", submittedBy="string", submittedOn="datetime", solvedOn="datetime"),
        "SolverConfiguration": E(status="string", description="string", avgLoad="float"),
        "StructuredProblemData": E(format="string", lin="string", quad="string", offset="float"),
        "StructuredProblemAnswer": E(format="string", activeVariables="string", energies="string", solutions="string", numOccurrences="string", numVariables="integer", timing="string"),
        "Region": E(code="string", name="string", endpoint="string"),
    },
    # Faithful Landsat STAC model (official stac-extensions/landsat JSON Schema +
    # stac-extensions/eo). The schema's OWN enum arrays enforced at the schema
    # version (dbt/freee discipline): collectionCategory(5)/collectionNumber(2)/
    # wrsType(2)/correction(5). eo commonName grew recently (green05/rededge07x)
    # -> gapped despite having an enum array.
    "landsat": {
        "LandsatItemProperties": E(sceneId="string", collectionCategory="string", collectionNumber="string", wrsType="string", wrsPath="string", wrsRow="string", cloudCoverLand="float", correction="string", productGenerated="datetime"),
        "StacAsset": E(href="string", title="string", description="string", type="string"),
        "InstrumentProperties": E(platform="string", constellation="string", mission="string", gsd="float"),
        "EoBandProperties": E(cloudCover="float", snowCover="float", commonName="string", centerWavelength="float", fullWidthHalfMax="float", solarIllumination="float"),
    },
    # Faithful Android platform model (official developer.android.com reference,
    # android.os.BatteryManager + android.os.Build). BATTERY_STATUS_* (1-5,
    # unchanged since API 1/2008) + BATTERY_HEALTH_* (1-7, stable since API 11)
    # enforced as integers. BATTERY_PLUGGED_* gapped: power-of-two values AND
    # DOCK=8 added in API 33 (2022) — both bitmask-shaped and version-growing.
    "android_aosp": {
        "BatteryStatus": E(status="integer", health="integer", plugged="integer", level="integer", scale="integer", temperature="integer", voltage="integer", present="boolean", technology="string"),
        "Build": E(board="string", brand="string", device="string", hardware="string", manufacturer="string", model="string", product="string", fingerprint="string"),
    },
}

# Faithful Argo ocean-float model (official Argo User's Manual, archimer
# doi:10.13155/29825 PDF text-extracted + the official NVS Argo vocabularies).
# direction {A,D} (physically anchored: a profile ascends or descends) +
# dataMode {R,A,D} (manual-defined complete lifecycle) + the QC flags
# (Reference table 2 = NVS RR2, {0,1,2,3,4,5,8,9} — 6,7 not defined) enforced.
PLATFORM_OVERRIDES["argo_ocean_floats"] = {
    "Profile": E(platformNumber="string", projectName="string", piName="string", cycleNumber="integer", direction="string", dataMode="string", juld="float", latitude="float", longitude="float", positionQc="integer", dataCentre="string"),
    "Measurement": E(pres="float", presQc="integer", temp="float", tempQc="integer", psal="float", psalQc="integer"),
    "Calibration": E(equation="string", coefficient="string", comment="string"),
}

# Faithful comma.ai (company) API model — verified against the official
# api.comma.ai documentation page. deviceType ('one of (neo, panda, app)'),
# primeType (0/1/2 documented complete), saveType (the page declares both a
# 2- and 3-value set; the documented superset favorite/recent/next is
# enforced) and the Segment File Status table (0/10/20/30/40) enforced.
PLATFORM_OVERRIDES["comma_ai"] = {
    "Device": E(dongleId="string", alias="string", serial="string", athenaHost="string", lastAthenaPing="integer", ignoreUploads="boolean", isPaired="boolean", isOwner="boolean", publicKey="string", prime="boolean", primeType="integer", trialClaimed="boolean", deviceType="string", lastGpsTime="integer", lastGpsLat="float", lastGpsLng="float", openpilotVersion="string", simId="string"),
    "Route": E(fullname="string", url="string", createTime="integer", startLat="float", startLng="float", endLat="float", endLng="float", radar="boolean", hpgps="boolean", passive="boolean", platform="string", version="string", gitRemote="string", gitBranch="string", gitCommit="string", gitDirty="boolean", maxlog="integer", proclog="integer", maxcamera="integer", proccamera="integer"),
    "Segment": E(canonicalName="string", number="integer", procLog="integer", procCamera="integer", procDcamera="integer", startTimeUtcMillis="integer", endTimeUtcMillis="integer"),
    "SavedLocation": E(placeName="string", placeDetails="string", latitude="float", longitude="float", saveType="string", label="string"),
    "User": E(email="string", points="integer", regdate="integer", superuser="boolean", username="string"),
}

# auterion joins the MAVLink family (4th member after mavlink_drones /
# mavlink_swarm / px4_autopilot): docs.auterion.com documents APX4 (Auterion's
# PX4-based flight stack) + MAVLink Forwarding as product features, and
# auterion.com states its PX4 contributions — official conformance.
PLATFORM_OVERRIDES["auterion"] = PLATFORM_OVERRIDES["mavlink_swarm"]

# freefly joins the MAVLink family (5th member) via the FIRST TRANSITIVE
# (2-hop) conformance chain: freeflysystems.com/astro officially describes
# Astro as running AuterionOS (title/og/JSON-LD/body, 4 occurrences), and
# Auterion's own docs establish AuterionOS = APX4 (PX4-based) + MAVLink.
# Each hop is an official self-declaration, independently fetched.
PLATFORM_OVERRIDES["freefly"] = PLATFORM_OVERRIDES["mavlink_swarm"]

# Faithful Airbyte protocol model (official airbytehq/airbyte-protocol
# v0/airbyte_protocol.yaml — machine-extracted enum arrays). Stable complete
# sets enforced (SyncMode dichotomy, log levels, connection status, state
# types, stream-status lifecycle); sets that grew WITHIN v0
# (AirbyteMessage.type +DESTINATION_CATALOG, DestinationSyncMode
# +update/soft_delete, meta-change reasons) -> gapped.
PLATFORM_OVERRIDES["airbyte"] = {
    "AirbyteMessage": E(type="string"),
    "AirbyteRecordMessage": E(stream="string", namespace="string", emittedAt="integer"),
    "AirbyteLogMessage": E(level="string", message="string", stackTrace="string"),
    "AirbyteConnectionStatus": E(status="string", message="string"),
    "AirbyteStateMessage": E(type="string"),
    "AirbyteStreamStatusTraceMessage": E(status="string"),
    "ConfiguredAirbyteStream": E(syncMode="string", destinationSyncMode="string", cursorField="string", primaryKey="string"),
}

# Faithful Agones model (official googleforgames/agones pkg/apis/agones/v1 Go
# sources). The v1 CRD is Kubernetes-compatibility-bound: GameServerState
# (11, complete state machine) + PortPolicy (4) + SdkServerLogLevel (4)
# enforced; struct fields machine-extracted from json tags.
PLATFORM_OVERRIDES["agones"] = {
    "GameServer": E(state="string", address="string", nodeName="string", reservedUntil="datetime", container="string", scheduling="string"),
    "GameServerPort": E(name="string", portPolicy="string", container="string", containerPort="integer", hostPort="integer", protocol="string"),
    "Fleet": E(replicas="integer", readyReplicas="integer", reservedReplicas="integer", allocatedReplicas="integer", scheduling="string"),
    "SdkServer": E(logLevel="string", grpcPort="integer", httpPort="integer"),
}

# Faithful ARM architecture model (official Arm docs via the
# documentation-service.arm.com JSON API — the JS-gated developer.arm.com
# pages are served verbatim there as base64 content, harness-fetchable).
# ISA-anchored closed sets enforced: condition-code suffixes (17, fixed by
# the 4-bit cond encoding incl. CS/HS + CC/LO aliases) and Exception levels
# (EL0-EL3 — 'there are four Exception levels', Arm's own learn-the-
# architecture doc). System registers / instruction lists are open-ended.
PLATFORM_OVERRIDES["arm_isa"] = {
    "ConditionCode": E(suffix="string", meaning="string"),
    "ExceptionLevel": E(level="string", typicalUsage="string"),
    "PrivilegeModel": E(name="string", description="string"),
}

# Faithful Cloud Firestore model (official Google Discovery document,
# firestore v1 — versioned API surface, machine-extracted enums). Stable
# sets enforced (direction/index state/index-field order+arrayConfig/
# nullValue); sets that grew WITHIN v1 (CompositeFilter.op +OR 2023,
# FieldFilter.op +NOT_IN, apiScope +MONGODB 2024, density 2024, queryScope)
# -> gapped per the airbyte in-place-evolution discipline.
PLATFORM_OVERRIDES["firebase"] = {
    "Document": E(name="string", createTime="datetime", updateTime="datetime"),
    "Value": E(booleanValue="boolean", stringValue="string", integerValue="integer", doubleValue="float", timestampValue="datetime", referenceValue="string", bytesValue="string", nullValue="string"),
    "Index": E(name="string", state="string", queryScope="string", apiScope="string", multikey="boolean", unique="boolean", shardCount="integer"),
    "IndexField": E(fieldPath="string", order="string", arrayConfig="string"),
    "Order": E(direction="string"),
}

# Faithful Google Compute Engine model (official Discovery document,
# compute v1 rev 20260520 — machine-extracted). Stable sets enforced
# (Firewall.direction INGRESS/EGRESS complete dichotomy; Operation.status
# DONE/PENDING/RUNNING stable since 2013). Instance.status gapped: grew
# within v1 (SUSPENDING/SUSPENDED 2021, REPAIRING) — firebase/airbyte
# in-place-evolution discipline; Disk.status/architecture/accessMode
# gapped (growth recency unconfirmed / young / arch could grow).
PLATFORM_OVERRIDES["gcp"] = {
    "Instance": E(name="string", machineType="string", status="string", zone="string", creationTimestamp="datetime", cpuPlatform="string", hostname="string", canIpForward="boolean", deletionProtection="boolean"),
    "Disk": E(name="string", sizeGb="string", status="string", type="string", zone="string", creationTimestamp="datetime", architecture="string"),
    "Firewall": E(name="string", network="string", direction="string", priority="integer", creationTimestamp="datetime", disabled="boolean"),
    "Network": E(name="string", description="string", autoCreateSubnetworks="boolean", mtu="integer", creationTimestamp="datetime"),
    "Operation": E(name="string", status="string", operationType="string", progress="integer", startTime="datetime", endTime="datetime", zone="string"),
}

# Faithful iOS SDK model (official Apple developer-docs JSON API:
# developer.apple.com/tutorials/data/documentation/uikit/*.json). 18-year
# anchors: UIDeviceOrientation (7 cases, stable since iOS 2/2008) +
# UIDevice.BatteryState (4) enforced; UIUserInterfaceStyle (3, stable
# since iOS 12/2018) enforced.
PLATFORM_OVERRIDES["ios_sdk"] = {
    "Device": E(name="string", model="string", systemName="string", systemVersion="string", batteryLevel="float", batteryState="string", orientation="string", identifierForVendor="string", isBatteryMonitoringEnabled="boolean"),
    "TraitCollection": E(userInterfaceStyle="string"),
    "Screen": E(scale="float", nativeScale="float", brightness="float", wantsSoftwareDimming="boolean", maximumFramesPerSecond="integer"),
}

# Faithful openFDA model (official open.fda.gov field-reference YAMLs — the
# FDA's own machine-readable field specs with explicit possible_values
# one_of closed-set declarations). 8 enum fields enforced from one_of
# declarations incl. the regulatory recall classification (Class I/II/III).
# The draft's status set ('Ongoing'/'Open') was REFUTED by the YAML
# ('On-Going'/'Pending'); product_type/reporttype/event_type were
# draft-gapped but spec-declared -> enforced (landsat rule).
PLATFORM_OVERRIDES["fda"] = {
    "DrugEvent": E(safetyreportid="string", transmissiondate="datetime", serious="string", seriousnessdeath="string", receivedate="datetime", receiptdate="datetime", occurcountry="string", reporttype="string", fulfillexpeditecriteria="string"),
    "EnforcementReport": E(eventId="string", status="string", classification="string", country="string", productDescription="string", productType="string", reasonForRecall="string", recallingFirm="string", recallNumber="string", reportDate="datetime", voluntaryMandated="string"),
    "DrugLabel": E(activeIngredient="string", adverseReactions="string", clinicalPharmacology="string", contraindications="string", description="string", dosageAndAdministration="string", indicationsAndUsage="string", warnings="string", version="string", effectiveTime="datetime"),
    "DeviceEvent": E(eventKey="string", eventType="string", dateOfEvent="datetime", reportNumber="string", adverseEventFlag="string", productProblemFlag="string", singleUseFlag="string", reprocessedAndReusedFlag="string", dateReport="datetime"),
}

# Faithful Losant model (official Losant/losant-rest-js JSON schemas — the
# operator's own published client schemas). 8 spec-declared enums enforced
# (freee/landsat rule: spec-declared enum arrays, no observed growth);
# method is additionally HTTP-verb-anchored.
PLATFORM_OVERRIDES["losant"] = {
    "Device": E(deviceId="string", applicationId="string", creationDate="datetime", lastUpdated="datetime", name="string", description="string", deviceClass="string", gatewayId="string"),
    "Application": E(applicationId="string", creationDate="datetime", lastUpdated="datetime", ownerId="string", ownerType="string", organizationName="string", name="string", description="string"),
    "Webhook": E(webhookId="string", applicationId="string", creationDate="datetime", lastUpdated="datetime", name="string", description="string", token="string", responseCode="integer", verificationType="string", castBuffersAs="string"),
    "ExperienceEndpoint": E(experienceEndpointId="string", applicationId="string", creationDate="datetime", lastUpdated="datetime", createdByType="string", lastUpdatedByType="string", method="string", access="string", description="string"),
    "ExperienceUser": E(experienceUserId="string", applicationId="string", creationDate="datetime", lastUpdated="datetime", passwordLastUpdated="datetime", lastLogin="datetime", email="string", firstName="string", lastName="string"),
}

# Faithful macOS/Darwin model (official Apple developer-docs JSON API).
# ComparisonResult (3, frozen since NeXTSTEP) + ProcessInfo.ThermalState
# (4: nominal/fair/serious/critical) enforced.
PLATFORM_OVERRIDES["macos_darwin"] = {
    "ProcessInfo": E(processName="string", processIdentifier="integer", operatingSystemVersionString="string", physicalMemory="integer", processorCount="integer", activeProcessorCount="integer", thermalState="string", isLowPowerModeEnabled="boolean", systemUptime="float"),
    "OperatingSystemVersion": E(majorVersion="integer", minorVersion="integer", patchVersion="integer"),
    "ComparisonResult": E(result="string"),
}

# Faithful Google Workspace Admin SDK model (official directory_v1 Discovery
# document, rev 20260602 — machine-extracted). osVersionCompliance(4,
# complete lifecycle) + chromeOsType(3, two OS variants + unspecified)
# enforced; deviceLicenseType(10, license tiers visibly accreted
# perpetual/fixedTerm variants) gapped; Member.role/type are plain strings
# (no enum) in the discovery doc -> no enum to enforce.
PLATFORM_OVERRIDES["google-workspace"] = {
    "User": E(primaryEmail="string", suspended="boolean", isAdmin="boolean", isDelegatedAdmin="boolean", orgUnitPath="string", creationTime="datetime", lastLoginTime="datetime", agreedToTerms="boolean", archived="boolean"),
    "Group": E(email="string", name="string", directMembersCount="string", adminCreated="boolean", description="string"),
    "Member": E(email="string", role="string", type="string", status="string"),
    "OrgUnit": E(name="string", orgUnitPath="string", parentOrgUnitPath="string", description="string", blockInheritance="boolean"),
    "ChromeOsDevice": E(serialNumber="string", status="string", chromeOsType="string", osVersionCompliance="string", deviceLicenseType="string", lastSync="datetime"),
}

# Faithful US Census Bureau API model (official api.census.gov machine-
# readable metadata: data.json catalog + per-dataset variables.json /
# geography.json). Dataset.accessLevel enforced from the Project Open Data
# v1.1 schema's own enum (public / restricted public / non-public).
# predicateType gapped (observed values, no declared closed set).
PLATFORM_OVERRIDES["censusgov"] = {
    "Dataset": E(title="string", description="string", identifier="string", accessLevel="string", modified="datetime", cVintage="integer", cIsAggregate="boolean", cIsCube="boolean", cIsAvailable="boolean"),
    "Variable": E(label="string", concept="string", predicateType="string", group="string", limit="integer"),
    "Geography": E(name="string", geoLevelDisplay="string", referenceDate="datetime"),
}

# Faithful IERS Earth-orientation model (the official finals2000A plain-text
# format specification, maia.usno.navy.mil/ser7/readme.finals2000A). The
# three IERS-or-Prediction flags {I,P} enforced — format-spec-anchored: the
# fixed-column format cannot change without breaking every parser worldwide.
PLATFORM_OVERRIDES["iers_earth_rotation"] = {
    "EopRecord": E(mjd="float", pmX="float", pmXError="float", pmY="float", pmYError="float", ut1MinusUtc="float", ut1Error="float", lod="float", lodError="float", dX="float", dY="float", polarMotionFlag="string", ut1Flag="string", nutationFlag="string"),
    "BulletinBValues": E(pmX="float", pmY="float", ut1MinusUtc="float", dX="float", dY="float"),
}

# Faithful Hologram IoT-SIM model (the operator's own official apiary.apib
# docs repo). euiccType(3) + euiccState(3) enforced (spec-declared complete);
# CellularLink.state REFUSED despite the field doc's LIVE/PAUSED/DEAD — the
# same spec uses transitional LIVE-PENDING / PAUSED-PENDING-USER values, so
# enforcing the subset would false-reject (Redis-TYPE lesson as a refusal).
PLATFORM_OVERRIDES["hologram"] = {
    "Device": E(orgid="integer", name="string", type="string", whencreated="datetime", phonenumber="string", tunnelable="boolean", imei="string", hidden="boolean"),
    "CellularLink": E(deviceid="integer", devicename="string", orgid="integer", sim="string", msisdn="string", state="string", whenclaimed="datetime", whenexpires="datetime", euiccType="string", euiccState="string"),
    "DataPlan": E(name="string", partnerid="integer", description="string", data="integer", recurring="boolean", enabled="boolean", billingperiod="integer"),
    "SmsRecord": E(linkid="integer", recordId="integer", timestamp="datetime", direction="string", otherNumber="string"),
    "Tag": E(name="string"),
}

# Faithful Google Ads model (official googleapis versioned protos, v24 —
# each vN dir is immutable on release, changes go to vN+1: the dbt-style
# anchor). CampaignStatus(5) + AdGroupStatus(5) + CampaignServingStatus(7)
# enforced at the v24 anchor; advertisingChannelType / adGroupType grow
# with product launches -> gapped.
PLATFORM_OVERRIDES["googleads"] = {
    "Campaign": E(name="string", status="string", servingStatus="string", advertisingChannelType="string", startDateTime="datetime", endDateTime="datetime", trackingUrlTemplate="string", baseCampaign="string"),
    "AdGroup": E(name="string", status="string", type="string", cpcBidMicros="integer", trackingUrlTemplate="string", baseAdGroup="string"),
}

# Faithful visionOS/SwiftUI model (official Apple docs JSON API).
# ScenePhase(3, closed lifecycle) + ImmersionStyle(4 documented static
# styles) enforced.
PLATFORM_OVERRIDES["apple_visionos"] = {
    "ScenePhase": E(phase="string"),
    "ImmersiveSpace": E(immersionStyle="string", systemOverlaysVisible="boolean"),
}

# Faithful JMA 防災情報XML model (the official xml.kishou.go.jp XSD schema
# zip — machine-readable — plus the normative format v1.3 PDF text-extracted
# per the argo precedent). Control.Status enforced (通常/訓練/試験,
# xs:enumeration in jmx.xsd); Head.InfoType enforced (発表/更新/訂正/取消 —
# declared complete in the format spec; the XSD types it as plain string).
PLATFORM_OVERRIDES["jma_weather"] = {
    "Control": E(title="string", dateTime="datetime", status="string", editorialOffice="string", publishingOffice="string"),
    "Head": E(title="string", reportDateTime="datetime", targetDateTime="datetime", validDateTime="datetime", eventID="string", infoType="string", serial="string", infoKind="string", infoKindVersion="string"),
}

# Faithful BIPM Circular T model (the official cirt files on
# webtai.bipm.org + the Explanatory Supplement PDF the Circular itself
# cites — text-extracted per the argo/jma precedent). Laboratory codes are
# an open registry (labs join/leave) -> no enum; fields verified against
# the live cirt.460 structure + supplement section definitions.
PLATFORM_OVERRIDES["bipm_utc"] = {
    "CircularT": E(number="integer", issueDate="datetime", issn="string", taiMinusUtc="integer"),
    "UtcDifference": E(laboratory="string", mjd="integer", utcMinusUtck="float", uncertaintyA="float", uncertaintyB="float", uncertaintyTotal="float"),
    "Laboratory": E(code="string", location="string"),
}

# Faithful ECB Data Portal API model (the official data-api.ecb.europa.eu
# help — declares the SDMX REST surface). detail enforced
# {full, dataonly, serieskeysonly, nodata} — all four declared with
# semantics in the official docs.
PLATFORM_OVERRIDES["ecb"] = {
    "DataQuery": E(flowRef="string", key="string", startPeriod="string", endPeriod="string", updatedAfter="datetime", firstNObservations="integer", lastNObservations="integer", detail="string", includeHistory="boolean"),
    "Dataflow": E(agencyID="string", version="string", name="string"),
    "Series": E(seriesKey="string", frequency="string", lastUpdated="datetime"),
}

# Faithful EPSG Geodetic Registry model (the official IOGP registry API at
# apps.epsg.org/api/v1 — field surfaces verified against live canonical
# entities 4326/6326/7030 per the original L5 method's real-object rule).
# Kind/Type/RealizationMethod are registry vocabularies without a fetched
# closed declaration -> gapped (live-observed != declared); a fields-
# verified L5 like bipm_utc.
PLATFORM_OVERRIDES["epsg_registry"] = {
    "CoordRefSystem": E(code="integer", name="string", kind="string", dataSource="string", informationSource="string", remark="string", revisionDate="datetime"),
    "Datum": E(code="integer", name="string", type="string", origin="string", publicationDate="datetime", realizationMethod="string", anchorEpoch="string", frameReferenceEpoch="string", revisionDate="datetime"),
    "Ellipsoid": E(code="integer", name="string", semiMajorAxis="float", semiMinorAxis="float", inverseFlattening="float", shape="string", unit="string", revisionDate="datetime"),
    "Usage": E(code="integer", name="string", scopeDetails="string"),
}

# SDMX 2.1 REST conformance family (the 4th family after FHIR/MAVLink/GBFS):
# agencies serving the official SDMX 2.1 REST surface join on the
# spec-verified model. The official sdmx-twg spec (v1.5.0 tag) declares
# detail {full, dataonly, serieskeysonly, nodata} — matching ECB's own docs
# (the family anchor, already L5). Conformance evidence: eurostat serves at
# .../api/dissemination/sdmx/2.1/ and IMF's api.imf.org/external/sdmx/2.1/
# returns SDMX-ML with the official v2_1 namespace (harness-fetched).
for _sdmx_agency in ("eurostat", "imf", "bis"):
    PLATFORM_OVERRIDES[_sdmx_agency] = PLATFORM_OVERRIDES["ecb"]

# Faithful EDINET API v2 model (金融庁の公式 API 仕様書 ESE140206 PDF,
# text-extracted per the argo/jma precedent). Nine flag/status enums
# enforced — every set is declared with per-value semantics in the spec
# (取下/修正/不開示/縦覧 statuses + 5 binary document flags, all string-
# typed "0"/"1"/... per the spec). docTypeCode gapped (様式コードリスト is
# a large separately-published table that tracks 府令 changes).
PLATFORM_OVERRIDES["edinet"] = {
    "Document": E(docID="string", edinetCode="string", secCode="string", jcn="string", filerName="string", fundCode="string", docTypeCode="string", periodStart="datetime", periodEnd="datetime", submitDateTime="datetime", docDescription="string", withdrawalStatus="string", docInfoEditStatus="string", disclosureStatus="string", xbrlFlag="string", pdfFlag="string", attachDocFlag="string", englishDocFlag="string", csvFlag="string", legalStatus="string"),
    "Metadata": E(title="string", parameterDate="datetime", parameterType="string", resultsetCount="integer", processDateTime="datetime", status="string", message="string"),
}

# Faithful Apigee model (the official Google Discovery document, rev
# 20260529, 342 schemas — machine-extracted). Complete lifecycle/type sets
# enforced (state CRUD lifecycle, CRUD operationType, scalar-type system,
# runtime/proxy/deployment types); product-coupled growable sets
# (TraceConfig.exporter, riskAssessmentType) gapped.
PLATFORM_OVERRIDES["apigee"] = {
    "Organization": E(name="string", customerName="string", runtimeType="string", state="string", subscriptionType="string", analyticsRegion="string", lastModifiedAt="integer", expiresAt="integer", networkEgressRestricted="boolean"),
    "Environment": E(name="string", displayName="string", state="string", apiProxyType="string", deploymentType="string", createdAt="integer", lastModifiedAt="integer", hasAttachedFlowHooks="boolean"),
    "ApiProxy": E(name="string", readOnly="boolean", apiProxyType="string", latestRevisionId="string", space="string"),
    "Deployment": E(apiProxy="string", environment="string", revision="string", state="string", proxyDeploymentType="string", deployStartTime="integer", serviceAccount="string"),
    "DataCollector": E(name="string", description="string", type="string", createdAt="integer", lastModifiedAt="integer"),
}

# Faithful Brightcove CMS model (the operator's own published OpenAPI 3.0.3
# at apis.support.brightcove.com — 52 schemas, machine-extracted). Eight
# spec-declared enums enforced incl. the Video state lifecycle(4), ingest
# lifecycle(5), playlist type(8, the complete smart-playlist algebra) and
# audio-track variant(5).
PLATFORM_OVERRIDES["brightcove"] = {
    "Video": E(name="string", description="string", state="string", economics="string", deliveryType="string", duration="integer", complete="boolean", createdAt="datetime", drmDisabled="boolean", hasDigitalMaster="boolean", folderId="string"),
    "IngestJobStatus": E(accountId="string", errorCode="string", errorMessage="string", priority="string", startedAt="datetime", state="string", submittedAt="datetime", updatedAt="datetime", videoId="string"),
    "Playlist": E(accountId="string", createdAt="datetime", description="string", favorite="boolean", name="string", referenceId="string", search="string", state="string", type="string"),
    "AudioTrack": E(duration="integer", isDefault="boolean", language="string", variant="string"),
}

# Faithful Chainlink data-feed model (the official AggregatorV3Interface
# from smartcontractkit/chainlink-brownie-contracts — frozen since 2020 by
# ON-CHAIN IMMUTABILITY: deployed feeds cannot change their interface, the
# strongest freeze in the corpus). Fields-verified; Solidity uint80/int256
# quantities modeled as strings.
PLATFORM_OVERRIDES["chainlink"] = {
    "PriceFeed": E(decimals="integer", description="string", version="integer", address="string"),
    "RoundData": E(roundId="string", answer="string", startedAt="integer", updatedAt="integer", answeredInRound="string"),
}

# Faithful Aptos model (the official aptos-core Node API OpenAPI, version
# 1.2.0, 188 schemas). MoveFunctionVisibility(3: private/public/friend —
# the Move LANGUAGE's visibility system, language-anchored) + RoleType(2:
# validator/full_node) enforced. U64s are strings per the Aptos wire
# convention.
PLATFORM_OVERRIDES["aptos_pos"] = {
    "Block": E(blockHeight="string", blockHash="string", blockTimestamp="string", firstVersion="string", lastVersion="string"),
    "LedgerInfo": E(chainId="integer", epoch="string", ledgerVersion="string", oldestLedgerVersion="string", ledgerTimestamp="string", nodeRole="string", blockHeight="string", gitHash="string"),
    "UserTransaction": E(version="string", hash="string", gasUsed="string", success="boolean", vmStatus="string", sender="string", sequenceNumber="string", maxGasAmount="string", gasUnitPrice="string"),
    "MoveFunction": E(name="string", visibility="string", isEntry="boolean", isView="boolean"),
    "AccountData": E(sequenceNumber="string", authenticationKey="string"),
}

# Ethereum JSON-RPC conformance family (the 5th family): node providers
# whose OWN docs document the standard eth_* JSON-RPC interface join on the
# official ethereum/execution-apis spec model. BlockTag(5, declared with
# per-value semantics) + Receipt.status(2, '1 (success) or 0 (failure)')
# enforced; hex quantities modeled as strings per the wire format.
_ETH_JSONRPC_MODEL = {
    "Block": E(hash="string", parentHash="string", miner="string", stateRoot="string", transactionsRoot="string", receiptsRoot="string", number="string", gasLimit="string", gasUsed="string", timestamp="string", baseFeePerGas="string", blobGasUsed="string", excessBlobGas="string"),
    "BlockQuery": E(blockTag="string", hydrated="boolean"),
    "Receipt": E(transactionHash="string", transactionIndex="string", blockHash="string", blockNumber="string", gasUsed="string", cumulativeGasUsed="string", contractAddress="string", status="string", effectiveGasPrice="string", type="string"),
}
for _eth_provider in ("infura", "alchemy"):
    PLATFORM_OVERRIDES[_eth_provider] = _ETH_JSONRPC_MODEL

# Faithful Kaltura model (the operator's own machine-readable API schema:
# kaltura.com/api_v3/api_schema.php, apiVersion 21.12.0). mediaType(7,
# legacy live-stream members fossilized) + moderationStatus(6, complete
# lifecycle) + sessionType(2) enforced as integers; entryStatus/entryType
# GAPPED — plugin extension values (virusScan.Infected, room.room) are
# mixed into the int sets (the openxr extension-bearing discipline).
PLATFORM_OVERRIDES["kaltura"] = {
    "BaseEntry": E(name="string", description="string", partnerId="integer", userId="string", creatorId="string", tags="string", status="string", moderationStatus="integer", moderationCount="integer"),
    "MediaEntry": E(mediaType="integer", sourceType="string", dataUrl="string", mediaDate="integer", creditUserName="string", creditUrl="string", conversionQuality="string", isTrimDisabled="integer"),
    "SessionInfo": E(ks="string", sessionType="integer", partnerId="integer", userId="string", expiry="integer", privileges="string"),
}

# Faithful Microsoft 365 (Graph v1.0) model — the official $metadata CSDL
# (graph.microsoft.com/v1.0/$metadata, 827 declared EnumTypes; v1.0 is the
# compatibility-bound surface). Outlook-era-stable enums enforced:
# importance(3)/bodyType(2)/sensitivity(4)/freeBusyStatus(6)/
# attendeeType(3)/responseType(6). calendarColor gapped (maxColor sentinel
# + theme growth).
PLATFORM_OVERRIDES["m365"] = {
    "Message": E(subject="string", bodyPreview="string", conversationId="string", hasAttachments="boolean", importance="string", isDraft="boolean", isRead="boolean", internetMessageId="string", parentFolderId="string", receivedDateTime="datetime", sentDateTime="datetime", webLink="string", bodyContentType="string"),
    "Event": E(subject="string", bodyPreview="string", importance="string", isAllDay="boolean", isCancelled="boolean", isDraft="boolean", isOnlineMeeting="boolean", isOrganizer="boolean", hideAttendees="boolean", iCalUId="string", showAs="string", sensitivity="string", onlineMeetingUrl="string"),
    "Attendee": E(type="string", status="string", emailAddress="string"),
}

# Faithful Azure Compute model (the official Azure/azure-rest-api-specs
# FROZEN stable snapshot 2025-11-01 ComputeRP.json, 428 definitions — the
# landsat/dbt-style immutable-version anchor). Five spec-declared enums
# enforced: priority(3)/evictionPolicy(2)/caching(3)/createOption(5)/
# statusLevel(3). vmSize is an open string (no enum upstream) — nothing
# fabricated.
PLATFORM_OVERRIDES["azure"] = {
    "VirtualMachine": E(vmId="string", provisioningState="string", priority="string", evictionPolicy="string", licenseType="string", extensionsTimeBudget="string", platformFaultDomain="integer", userData="string", timeCreated="datetime", vmSize="string"),
    "OsDisk": E(osType="string", name="string", caching="string", writeAcceleratorEnabled="boolean", createOption="string", diskSizeGB="integer", deleteOption="string"),
    "InstanceViewStatus": E(code="string", level="string", displayStatus="string", message="string", time="datetime"),
}

# Faithful AWS EC2 model (the official AWS-published wire model: botocore
# service-2.json, apiVersion 2016-11-15 — date-versioned and additive).
# Lifecycle enums enforced (InstanceStateName 6 / VolumeState 6 / VpcState 2
# — unchanged for a decade) + Tenancy(3, stable since 2015) +
# HypervisorType(2). InstanceType (1,212 values!) / VolumeType (gp3/io2
# additions) / Architecture (arm64_mac 2021) -> gapped as growing.
PLATFORM_OVERRIDES["aws"] = {
    "Instance": E(instanceId="string", instanceType="string", state="string", architecture="string", hypervisor="string", ebsOptimized="boolean", enaSupport="boolean", rootDeviceName="string", rootDeviceType="string", outpostArn="string"),
    "Volume": E(volumeId="string", size="integer", state="string", volumeType="string", iops="integer", throughput="integer", multiAttachEnabled="boolean", fastRestored="boolean", createTime="datetime"),
    "Vpc": E(vpcId="string", state="string", cidrBlock="string", isDefault="boolean", ownerId="string", instanceTenancy="string", dhcpOptionsId="string"),
    "SecurityGroup": E(groupId="string", groupName="string", description="string", vpcId="string", ownerId="string", securityGroupArn="string"),
}

# Faithful FDIC BankFind Suite model (the official banks.data.fdic.gov API;
# field surfaces from live entities per the real-object rule — 27,835
# institutions live). BKCLASS/RESTYPE values observed-not-declared (the
# property YAMLs are SPA-walled) -> fields-verified, enums gapped.
PLATFORM_OVERRIDES["fdic"] = {
    "Institution": E(name="string", cert="integer", city="string", stname="string", zip="string", bkclass="string", active="boolean", charter="string", insdate="datetime", effdate="datetime", webaddr="string"),
    "Failure": E(name="string", cert="integer", city="string", faildate="datetime", failyr="integer", restype="string", cost="float", qbfdep="float", qbfasset="float", savr="string"),
}

# GBFS conformance-leverage family (MAVLink/FHIR-family pattern): operators that
# OFFICIALLY serve public GBFS feeds from their own domains (per the official
# MobilityData systems.csv registry + live feed verification) join on the
# gbfs-verified model. Bird: 124 feeds on mds.bird.co; Lime: 47 on
# data.lime.bike; Dott: 350 on gbfs.api.ridedott.com.
for _gbfs_operator in ("bird_scooters", "lime_scooters", "dott"):
    PLATFORM_OVERRIDES[_gbfs_operator] = PLATFORM_OVERRIDES["gbfs"]

# ---------------------------------------------------------------------------
# 4. Code generation.
# ---------------------------------------------------------------------------

PY_TYPE_DEFAULT = {
    "string": '""', "integer": "0", "float": "0.0",
    "boolean": "False", "datetime": "now()",
}


def kotoba_schema(platform, ns, model):
    lines = [f"// {platform.capitalize()} clean-room schema -> Datomic EAVT mapping",
             f"// Generated by deepen_actors.py (ADR 260607 deepening phase).",
             "", f"namespace {ns} {{", ""]
    for ent, fields in model.items():
        lines.append(f"    entity {ent} {{")
        lines.append("        id: string @unique")
        for fname, ftype in fields.items():
            lines.append(f"        {fname}: {ftype}")
        lines.append("        createdAt: datetime")
        lines.append("        updatedAt: datetime")
        lines.append("    }")
        lines.append("")
    lines.append("}")
    return "\n".join(lines) + "\n"


def _coerce_expr(ftype, varexpr):
    if ftype == "integer":
        return f"int({varexpr} or 0)"
    if ftype == "float":
        return f"float({varexpr} or 0)"
    if ftype == "boolean":
        return f"bool({varexpr})"
    return f"{varexpr}"


def main_py(platform, ns, model):
    """Generate a CRUD WASM entrypoint covering every entity in the model."""
    id_prefix = re.sub(r"[^a-z0-9]", "", platform.lower())[:8] or "obj"
    out = []
    out.append('"""')
    out.append(f"Py Kotodama WASM entrypoint for the {platform.capitalize()} clean-room actor.")
    out.append("")
    out.append("Clean-room, API-shaped CRUD over a Datomic-backed Kotoba schema.")
    out.append("Generated by 70-tools/deepen_actors.py (ADR 260607 deepening phase).")
    out.append("No proprietary code or credentials; resource shapes only.")
    out.append('"""')
    out.append("from kotodama import Runtime")
    out.append("from kotoba import load_schema")
    out.append("from datomic import DatomicClient")
    out.append("import uuid")
    out.append("import datetime")
    out.append("")
    out.append(f'schema = load_schema("../schema/{platform}.kotoba")')
    out.append("db = DatomicClient.connect()")
    out.append(f'app = Runtime("{platform}-compat")')
    out.append("")
    out.append("")
    out.append("def now():")
    out.append("    return datetime.datetime.utcnow().isoformat()")
    out.append("")
    out.append("")
    out.append("def new_id(prefix):")
    out.append('    return f"{prefix}_" + uuid.uuid4().hex[:16]')
    out.append("")
    out.append("")
    out.append("def _persist(entity, rec):")
    out.append('    """Transact a record into Datomic as namespaced EAVT facts."""')
    out.append("    facts = {}")
    out.append("    for k, v in rec.items():")
    out.append(f'        facts[f"{ns}.{{entity}}/{{k}}"] = v')
    out.append("    db.transact([facts])")
    out.append("    return rec")
    out.append("")
    out.append("")
    out.append("def _query(entity, eid=None):")
    out.append('    """Read records of an entity from Datomic (optionally by id)."""')
    out.append(f'    pattern = {{"entity": f"{ns}.{{entity}}"}}')
    out.append("    if eid is not None:")
    out.append('        pattern["id"] = eid')
    out.append("    return db.query(pattern)")
    out.append("")
    out.append("")
    out.append("def _require(data, fields):")
    out.append("    missing = [f for f in fields if not data.get(f)]")
    out.append("    if missing:")
    out.append('        return {"error": {"message": "Missing required fields: " + ", ".join(missing)}}')
    out.append("    return None")
    out.append("")

    for ent, fields in model.items():
        plural = _pluralize(ent)
        route = f"/v1/{plural.lower()}"
        prefix = f"{id_prefix}_{ent[:3].lower()}"
        required = _required_fields(fields)
        # CREATE
        out.append("")
        out.append(f'@app.route("{route}", methods=["POST"])')
        out.append(f"def create_{_snake(ent)}(request):")
        out.append(f'    """Create a {ent}."""')
        out.append("    data = request.json or request.form or {}")
        if required:
            out.append(f"    err = _require(data, {required!r})")
            out.append("    if err:")
            out.append("        return err, 400")
        out.append(f'    rec = {{"id": new_id("{prefix}")}}')
        for fname, ftype in fields.items():
            out.append(f'    rec["{fname}"] = {_coerce_expr(ftype, f"data.get({fname!r})")}')
        out.append('    rec["createdAt"] = now()')
        out.append('    rec["updatedAt"] = rec["createdAt"]')
        out.append(f'    _persist("{ent}", rec)')
        out.append("    return rec, 201")
        # LIST
        out.append("")
        out.append(f'@app.route("{route}", methods=["GET"])')
        out.append(f"def list_{_snake(plural)}(request):")
        out.append(f'    """List {plural}."""')
        out.append(f'    items = _query("{ent}")')
        out.append('    return {"object": "list", "data": items, "count": len(items)}, 200')
        # GET
        out.append("")
        out.append(f'@app.route("{route}/<eid>", methods=["GET"])')
        out.append(f"def get_{_snake(ent)}(request, eid):")
        out.append(f'    """Retrieve a {ent} by id."""')
        out.append(f'    rows = _query("{ent}", eid)')
        out.append("    if not rows:")
        out.append('        return {"error": {"message": "Not found"}}, 404')
        out.append("    return rows[0], 200")
        # UPDATE
        out.append("")
        out.append(f'@app.route("{route}/<eid>", methods=["POST", "PATCH"])')
        out.append(f"def update_{_snake(ent)}(request, eid):")
        out.append(f'    """Update a {ent}."""')
        out.append(f'    rows = _query("{ent}", eid)')
        out.append("    if not rows:")
        out.append('        return {"error": {"message": "Not found"}}, 404')
        out.append("    data = request.json or request.form or {}")
        out.append("    rec = rows[0]")
        out.append("    for k, v in data.items():")
        out.append("        if k in rec and k not in (\"id\", \"createdAt\"):")
        out.append("            rec[k] = v")
        out.append('    rec["updatedAt"] = now()')
        out.append(f'    _persist("{ent}", rec)')
        out.append("    return rec, 200")
        # DELETE
        out.append("")
        out.append(f'@app.route("{route}/<eid>", methods=["DELETE"])')
        out.append(f"def delete_{_snake(ent)}(request, eid):")
        out.append(f'    """Delete a {ent}."""')
        out.append(f'    rows = _query("{ent}", eid)')
        out.append("    if not rows:")
        out.append('        return {"error": {"message": "Not found"}}, 404')
        out.append(f'    db.retract({{"entity": f"{ns}.{ent}", "id": eid}})')
        out.append('    return {"id": eid, "deleted": True}, 200')

    # healthz
    out.append("")
    out.append('@app.route("/healthz", methods=["GET"])')
    out.append("def healthz(request):")
    entity_names = list(model.keys())
    out.append(f'    return {{"status": "ok", "actor": "{platform}-compat", "entities": {entity_names!r}}}, 200')
    out.append("")
    out.append("")
    out.append('if __name__ == "__main__":')
    out.append("    app.start()")
    return "\n".join(out) + "\n"


def _required_fields(fields):
    """First 1-2 non-relational fields treated as required for validation."""
    req = []
    for fname, ftype in fields.items():
        if fname.endswith("Id") or fname.endswith("Ref"):
            continue
        req.append(fname)
        if len(req) >= 2:
            break
    return req


def _snake(name):
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def _pluralize(name):
    if name.endswith("y") and name[-2:-1] not in "aeiou":
        return name[:-1] + "ies"
    if name.endswith(("s", "x", "z", "ch", "sh")):
        return name + "es"
    return name + "s"


# ---------------------------------------------------------------------------
# 5. Driver.
# ---------------------------------------------------------------------------

def deepen(only=None, dry_run=False):
    os.chdir(ROOT)
    cats = parse_platform_categories()
    actor_dirs = sorted(d for d in os.listdir(ACTORS_DIR) if d.endswith("-compat"))
    written, skipped = 0, []
    for actor in actor_dirs:
        platform = actor[:-len("-compat")]
        if only and platform not in only:
            continue
        pkey = platform.strip()
        ns = re.sub(r"[^a-z0-9_]", "_", pkey.lower()) or "actor"
        model = (PLATFORM_OVERRIDES.get(pkey)
                 or CATEGORY_MODELS.get(cats.get(pkey))
                 or CATEGORY_MODELS.get(cats.get(platform)))
        if not model:
            # Unknown category (e.g. a future wave whose comment is not yet
            # mapped): fall back to a generic-but-multi-entity resource model
            # so the actor still reaches L3 rather than staying L1 boilerplate.
            skipped.append(platform)
            model = GENERIC_MODEL
        adir = os.path.join(ACTORS_DIR, actor)
        sdir = os.path.join(adir, "schema")
        srcdir = os.path.join(adir, "src")
        if dry_run:
            written += 1
            continue
        os.makedirs(sdir, exist_ok=True)
        os.makedirs(srcdir, exist_ok=True)
        with open(os.path.join(sdir, f"{platform}.kotoba"), "w") as f:
            f.write(kotoba_schema(platform, ns, model))
        with open(os.path.join(srcdir, "main.py"), "w") as f:
            f.write(main_py(platform, ns, model))
        written += 1
    print(f"Deepened {written} actors.")
    if skipped:
        print(f"UNMAPPED -> generic fallback ({len(skipped)}): "
              f"{', '.join(sorted(skipped))}")
        print("  (add their wave category to COMMENT_TO_KEY for a domain model.)")
    return skipped


if __name__ == "__main__":
    only = None
    dry = "--dry-run" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if args:
        only = set(args)
    deepen(only=only, dry_run=dry)
