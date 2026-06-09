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
}

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
