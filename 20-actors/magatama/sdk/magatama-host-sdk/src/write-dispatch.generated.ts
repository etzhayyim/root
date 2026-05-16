// Auto-generated dispatch table — DO NOT EDIT.
// Maps WriteBufferEntry `type` field → XRPC NSID.
// Originally WIT-generated; retained as hand-maintained after F-Plan F2 (2026-04-13).
// PdsInternalFn parameter archived 2026-04-13 (all dispatch is XRPC-only).
// Source of truth for new write types: add the case directly to dispatchWriteEntry() below
// and register the corresponding lexicon JSON under 00-contracts/lexicons/ai/gftd/apps/.

import type { WriteBufferEntry } from "./types.js";

type XrpcFn = (nsid: string, payload: unknown) => Promise<void>;

/**
 * Auto-generated dispatch for 777 write buffer entry types.
 * Each case maps a WIT @kind write func to its XRPC NSID.
 */
export async function dispatchWriteEntry(
  entry: WriteBufferEntry,
  xrpc: XrpcFn,
): Promise<void> {
  switch (entry.type) {

    // ── magatama:telemetry/access-log@1.0.0 ──
    // magatama:telemetry/access-log@1.0.0#counter-add
    case "access-log-counter-add":
      return xrpc("ai.gftd.telemetry.counterAdd", entry.payload);
    // magatama:telemetry/access-log@1.0.0#gauge-set
    case "access-log-gauge-set":
      return xrpc("ai.gftd.telemetry.gaugeSet", entry.payload);
    // magatama:telemetry/access-log@1.0.0#histogram-record
    case "access-log-histogram-record":
      return xrpc("ai.gftd.telemetry.histogramRecord", entry.payload);
    // magatama:telemetry/access-log@1.0.0#page-views
    case "access-log-page-views":
      return xrpc("ai.gftd.telemetry.pageViews", entry.payload);
    // magatama:telemetry/access-log@1.0.0#total-requests
    case "access-log-total-requests":
      return xrpc("ai.gftd.telemetry.totalRequests", entry.payload);

    // ── magatama:workflow/activity@1.0.0 ──
    // magatama:workflow/activity@1.0.0#await-all
    case "activity-await-all":
      return xrpc("ai.gftd.workflow.awaitAll", entry.payload);
    // magatama:workflow/activity@1.0.0#create-timer
    case "activity-create-timer":
      return xrpc("ai.gftd.workflow.createTimer", entry.payload);
    // magatama:workflow/activity@1.0.0#get
    case "activity-get":
      return xrpc("ai.gftd.workflow.get", entry.payload);
    // magatama:workflow/activity@1.0.0#heartbeat
    case "activity-heartbeat":
      return xrpc("ai.gftd.workflow.heartbeat", entry.payload);
    // magatama:workflow/activity@1.0.0#pause
    case "activity-pause":
      return xrpc("ai.gftd.workflow.pause", entry.payload);
    // magatama:workflow/activity@1.0.0#purge
    case "activity-purge":
      return xrpc("ai.gftd.workflow.purge", entry.payload);
    // magatama:workflow/activity@1.0.0#query
    case "activity-query":
      return xrpc("ai.gftd.workflow.query", entry.payload);
    // magatama:workflow/activity@1.0.0#raise-event
    case "activity-raise-event":
      return xrpc("ai.gftd.workflow.raiseEvent", entry.payload);
    // magatama:workflow/activity@1.0.0#resume
    case "activity-resume":
      return xrpc("ai.gftd.workflow.resume", entry.payload);
    // magatama:workflow/activity@1.0.0#schedule
    case "activity-schedule":
      return xrpc("ai.gftd.workflow.schedule", entry.payload);
    // magatama:workflow/activity@1.0.0#signal
    case "activity-signal":
      return xrpc("ai.gftd.workflow.signal", entry.payload);
    // magatama:workflow/activity@1.0.0#start
    case "activity-start":
      return xrpc("ai.gftd.workflow.start", entry.payload);
    // magatama:workflow/activity@1.0.0#submit-dag
    case "activity-submit-dag":
      return xrpc("ai.gftd.workflow.submitDag", entry.payload);
    // magatama:workflow/activity@1.0.0#terminate
    case "activity-terminate":
      return xrpc("ai.gftd.workflow.terminate", entry.payload);

    // ── chat-bsky:actor/actor@1.0.0 ──
    // chat-bsky:actor/actor@1.0.0#delete-account
    case "actor-delete-account":
      return xrpc("ai.gftd.apps.actor.deleteAccount", entry.payload);
    // chat-bsky:actor/actor@1.0.0#export-account-data
    case "actor-export-account-data":
      return xrpc("ai.gftd.apps.actor.exportAccountData", entry.payload);
    // app-bsky:actor/actor@1.0.0#put-preferences
    case "actor-put-preferences":
      return xrpc("ai.gftd.apps.actor.putPreferences", entry.payload);
    // magatama:actor/actor-state@1.0.0#cancel-schedule
    case "actor-state-cancel-schedule":
      return xrpc("ai.gftd.actor.cancelSchedule", entry.payload);
    // magatama:actor/actor-state@1.0.0#deactivate
    case "actor-state-deactivate":
      return xrpc("ai.gftd.actor.deactivate", entry.payload);
    // magatama:actor/actor-state@1.0.0#delete
    case "actor-state-delete":
      return xrpc("ai.gftd.actor.delete", entry.payload);
    // magatama:actor/actor-state@1.0.0#get
    case "actor-state-get":
      return xrpc("ai.gftd.actor.get", entry.payload);
    // magatama:actor/actor-state@1.0.0#invoke
    case "actor-state-invoke":
      return xrpc("ai.gftd.actor.invoke", entry.payload);
    // magatama:actor/actor-state@1.0.0#put
    case "actor-state-put":
      return xrpc("ai.gftd.actor.put", entry.payload);
    // magatama:actor/actor-state@1.0.0#register
    case "actor-state-register":
      return xrpc("ai.gftd.actor.register", entry.payload);
    // magatama:actor/actor-state@1.0.0#renew
    case "actor-state-renew":
      return xrpc("ai.gftd.actor.renew", entry.payload);
    // magatama:actor/actor-state@1.0.0#schedule-method
    case "actor-state-schedule-method":
      return xrpc("ai.gftd.actor.scheduleMethod", entry.payload);
    // magatama:actor/actor-state@1.0.0#try-lock
    case "actor-state-try-lock":
      return xrpc("ai.gftd.actor.tryLock", entry.payload);
    // magatama:actor/actor-state@1.0.0#unlock
    case "actor-state-unlock":
      return xrpc("ai.gftd.actor.unlock", entry.payload);
    // magatama:actor/actor-state@1.0.0#unregister
    case "actor-state-unregister":
      return xrpc("ai.gftd.actor.unregister", entry.payload);

    // ── com-atproto:admin/admin@1.0.0 ──
    // com-atproto:admin/admin@1.0.0#delete-account
    case "admin-delete-account":
      return xrpc("ai.gftd.apps.admin.deleteAccount", entry.payload);
    // com-atproto:admin/admin@1.0.0#disable-account-invites
    case "admin-disable-account-invites":
      return xrpc("ai.gftd.apps.admin.disableAccountInvites", entry.payload);
    // com-atproto:admin/admin@1.0.0#disable-invite-codes
    case "admin-disable-invite-codes":
      return xrpc("ai.gftd.apps.admin.disableInviteCodes", entry.payload);
    // com-atproto:admin/admin@1.0.0#enable-account-invites
    case "admin-enable-account-invites":
      return xrpc("ai.gftd.apps.admin.enableAccountInvites", entry.payload);
    // com-atproto:admin/admin@1.0.0#send-email
    case "admin-send-email":
      return xrpc("ai.gftd.apps.admin.sendEmail", entry.payload);
    // com-atproto:admin/admin@1.0.0#update-account-email
    case "admin-update-account-email":
      return xrpc("ai.gftd.apps.admin.updateAccountEmail", entry.payload);
    // com-atproto:admin/admin@1.0.0#update-account-handle
    case "admin-update-account-handle":
      return xrpc("ai.gftd.apps.admin.updateAccountHandle", entry.payload);
    // com-atproto:admin/admin@1.0.0#update-account-password
    case "admin-update-account-password":
      return xrpc("ai.gftd.apps.admin.updateAccountPassword", entry.payload);
    // com-atproto:admin/admin@1.0.0#update-account-signing-key
    case "admin-update-account-signing-key":
      return xrpc("ai.gftd.apps.admin.updateAccountSigningKey", entry.payload);
    // com-atproto:admin/admin@1.0.0#update-subject-status
    case "admin-update-subject-status":
      return xrpc("ai.gftd.apps.admin.updateSubjectStatus", entry.payload);

    // ── app-bsky:ageassurance/ageassurance@1.0.0 ──
    // app-bsky:ageassurance/ageassurance@1.0.0#begin
    case "ageassurance-begin":
      return xrpc("ai.gftd.apps.ageassurance.begin", entry.payload);

    // ── magatama:agent/agent@1.0.0 ──
    // magatama:agent/agent@1.0.0#chat
    case "agent-chat":
      return xrpc("ai.gftd.agent.chat", entry.payload);
    // magatama:agent/agent@1.0.0#converse
    case "agent-converse":
      return xrpc("ai.gftd.agent.converse", entry.payload);
    // magatama:agent/agent@1.0.0#get
    case "agent-get":
      return xrpc("ai.gftd.agent.get", entry.payload);
    // magatama:agent/agent@1.0.0#install
    case "agent-install":
      return xrpc("ai.gftd.agent.install", entry.payload);
    // magatama:agent/agent@1.0.0#invoke-tool
    case "agent-invoke-tool":
      return xrpc("ai.gftd.agent.invokeTool", entry.payload);
    // magatama:agent/agent@1.0.0#react
    case "agent-react":
      return xrpc("ai.gftd.agent.react", entry.payload);
    // magatama:agent/agent@1.0.0#register-manifest
    case "agent-register-manifest":
      return xrpc("ai.gftd.agent.registerManifest", entry.payload);
    // magatama:agent/agent@1.0.0#register-tools
    case "agent-register-tools":
      return xrpc("ai.gftd.agent.registerTools", entry.payload);
    // magatama:agent/agent@1.0.0#route
    case "agent-route":
      return xrpc("ai.gftd.agent.route", entry.payload);
    // magatama:agent/agent@1.0.0#uninstall
    case "agent-uninstall":
      return xrpc("ai.gftd.agent.uninstall", entry.payload);

    // ── magatama:contract/agreement@1.0.0 ──
    // magatama:contract/agreement@1.0.0#bind-performer
    case "agreement-bind-performer":
      return xrpc("ai.gftd.contract.bindPerformer", entry.payload);
    // magatama:contract/agreement@1.0.0#register-contract
    case "agreement-register-contract":
      return xrpc("ai.gftd.contract.registerContract", entry.payload);
    // magatama:contract/agreement@1.0.0#register-dependency
    case "agreement-register-dependency":
      return xrpc("ai.gftd.contract.registerDependency", entry.payload);
    // magatama:contract/agreement@1.0.0#resolve-graph
    case "agreement-resolve-graph":
      return xrpc("ai.gftd.contract.resolveGraph", entry.payload);

    // ── magatama:browser/analyzer@1.0.0 ──
    // magatama:browser/analyzer@1.0.0#analyze
    case "analyzer-analyze":
      return xrpc("ai.gftd.browser.analyze", entry.payload);
    // magatama:browser/analyzer@1.0.0#batch-fetch
    case "analyzer-batch-fetch":
      return xrpc("ai.gftd.browser.batchFetch", entry.payload);
    // magatama:browser/analyzer@1.0.0#click
    case "analyzer-click":
      return xrpc("ai.gftd.browser.click", entry.payload);
    // magatama:browser/analyzer@1.0.0#close-session
    case "analyzer-close-session":
      return xrpc("ai.gftd.browser.closeSession", entry.payload);
    // magatama:browser/analyzer@1.0.0#current-url
    case "analyzer-current-url":
      return xrpc("ai.gftd.browser.currentUrl", entry.payload);
    // magatama:browser/analyzer@1.0.0#eval-js
    case "analyzer-eval-js":
      return xrpc("ai.gftd.browser.evalJs", entry.payload);
    // magatama:browser/analyzer@1.0.0#extract-attr
    case "analyzer-extract-attr":
      return xrpc("ai.gftd.browser.extractAttr", entry.payload);
    // magatama:browser/analyzer@1.0.0#extract-links
    case "analyzer-extract-links":
      return xrpc("ai.gftd.browser.extractLinks", entry.payload);
    // magatama:browser/analyzer@1.0.0#extract-structured
    case "analyzer-extract-structured":
      return xrpc("ai.gftd.browser.extractStructured", entry.payload);
    // magatama:browser/analyzer@1.0.0#extract-table
    case "analyzer-extract-table":
      return xrpc("ai.gftd.browser.extractTable", entry.payload);
    // magatama:browser/analyzer@1.0.0#extract-text
    case "analyzer-extract-text":
      return xrpc("ai.gftd.browser.extractText", entry.payload);
    // magatama:browser/analyzer@1.0.0#fetch-html
    case "analyzer-fetch-html":
      return xrpc("ai.gftd.browser.fetchHtml", entry.payload);
    // magatama:browser/analyzer@1.0.0#is-visible
    case "analyzer-is-visible":
      return xrpc("ai.gftd.browser.isVisible", entry.payload);
    // magatama:browser/analyzer@1.0.0#navigate
    case "analyzer-navigate":
      return xrpc("ai.gftd.browser.navigate", entry.payload);
    // magatama:browser/analyzer@1.0.0#open-session
    case "analyzer-open-session":
      return xrpc("ai.gftd.browser.openSession", entry.payload);
    // magatama:browser/analyzer@1.0.0#page-html
    case "analyzer-page-html":
      return xrpc("ai.gftd.browser.pageHtml", entry.payload);
    // magatama:browser/analyzer@1.0.0#press-key
    case "analyzer-press-key":
      return xrpc("ai.gftd.browser.pressKey", entry.payload);
    // magatama:browser/analyzer@1.0.0#scrape-and-store
    case "analyzer-scrape-and-store":
      return xrpc("ai.gftd.browser.scrapeAndStore", entry.payload);
    // magatama:browser/analyzer@1.0.0#screenshot
    case "analyzer-screenshot":
      return xrpc("ai.gftd.browser.screenshot", entry.payload);
    // magatama:browser/analyzer@1.0.0#scroll
    case "analyzer-scroll":
      return xrpc("ai.gftd.browser.scroll", entry.payload);
    // magatama:browser/analyzer@1.0.0#select-option
    case "analyzer-select-option":
      return xrpc("ai.gftd.browser.selectOption", entry.payload);
    // magatama:browser/analyzer@1.0.0#set-cookies
    case "analyzer-set-cookies":
      return xrpc("ai.gftd.browser.setCookies", entry.payload);
    // magatama:browser/analyzer@1.0.0#type-text
    case "analyzer-type-text":
      return xrpc("ai.gftd.browser.typeText", entry.payload);
    // magatama:browser/analyzer@1.0.0#wait-for-navigation
    case "analyzer-wait-for-navigation":
      return xrpc("ai.gftd.browser.waitForNavigation", entry.payload);
    // magatama:browser/analyzer@1.0.0#wait-for-selector
    case "analyzer-wait-for-selector":
      return xrpc("ai.gftd.browser.waitForSelector", entry.payload);

    // ── magatama:audit/anomaly@1.0.0 ──
    // magatama:audit/anomaly@1.0.0#ack-alert
    case "anomaly-ack-alert":
      return xrpc("ai.gftd.audit.ackAlert", entry.payload);
    // magatama:audit/anomaly@1.0.0#add-object-edge
    case "anomaly-add-object-edge":
      return xrpc("ai.gftd.audit.addObjectEdge", entry.payload);
    // magatama:audit/anomaly@1.0.0#declare-incident
    case "anomaly-declare-incident":
      return xrpc("ai.gftd.audit.declareIncident", entry.payload);
    // magatama:audit/anomaly@1.0.0#emit-event
    case "anomaly-emit-event":
      // Legacy endpoint removed on PDS side; keep best-effort and avoid noisy 404 spam.
      return;
    // magatama:audit/anomaly@1.0.0#export-json
    case "anomaly-export-json":
      return xrpc("ai.gftd.audit.exportJson", entry.payload);
    // magatama:audit/anomaly@1.0.0#register-rule
    case "anomaly-register-rule":
      return xrpc("ai.gftd.audit.registerRule", entry.payload);
    // magatama:audit/anomaly@1.0.0#remove-rule
    case "anomaly-remove-rule":
      return xrpc("ai.gftd.audit.removeRule", entry.payload);
    // magatama:audit/anomaly@1.0.0#set-sla
    case "anomaly-set-sla":
      return xrpc("ai.gftd.audit.setSla", entry.payload);
    // magatama:audit/anomaly@1.0.0#update-incident
    case "anomaly-update-incident":
      return xrpc("ai.gftd.audit.updateIncident", entry.payload);
    // magatama:audit/anomaly@1.0.0#upsert-object
    case "anomaly-upsert-object":
      return xrpc("ai.gftd.audit.upsertObject", entry.payload);

    // ── magatama:auth/authn@1.0.0 ──
    // magatama:auth/authn@1.0.0#authorize
    case "authn-authorize":
      return xrpc("ai.gftd.auth.authorize", entry.payload);
    // magatama:auth/authn@1.0.0#ensure-active-session
    case "authn-ensure-active-session":
      return xrpc("ai.gftd.auth.ensureActiveSession", entry.payload);
    // magatama:auth/authn@1.0.0#resolve-context
    case "authn-resolve-context":
      return xrpc("ai.gftd.auth.resolveContext", entry.payload);
    // magatama:auth/authn@1.0.0#sha256
    case "authn-sha256":
      return xrpc("ai.gftd.auth.sha256", entry.payload);
    // magatama:auth/authn@1.0.0#sha256-hex
    case "authn-sha256-hex":
      return xrpc("ai.gftd.auth.sha256Hex", entry.payload);
    // magatama:auth/authn@1.0.0#verify-token
    case "authn-verify-token":
      return xrpc("ai.gftd.auth.verifyToken", entry.payload);
    // magatama:auth/authn@1.0.0#verify-token-with-azp
    case "authn-verify-token-with-azp":
      return xrpc("ai.gftd.auth.verifyTokenWithAzp", entry.payload);

    // ── app-bsky:bookmark/bookmark@1.0.0 ──
    // app-bsky:bookmark/bookmark@1.0.0#create-bookmark
    case "bookmark-create-bookmark":
      return xrpc("ai.gftd.apps.bookmark.createBookmark", entry.payload);
    // app-bsky:bookmark/bookmark@1.0.0#delete-bookmark
    case "bookmark-delete-bookmark":
      return xrpc("ai.gftd.apps.bookmark.deleteBookmark", entry.payload);

    // ── magatama:bpmn/bpmn@1.0.0 ──
    // magatama:bpmn/bpmn@1.0.0#broadcast-signal
    case "bpmn-broadcast-signal":
      return xrpc("ai.gftd.bpmn.broadcastSignal", entry.payload);
    // magatama:bpmn/bpmn@1.0.0#cancel
    case "bpmn-cancel":
      return xrpc("ai.gftd.bpmn.cancel", entry.payload);
    // magatama:bpmn/bpmn@1.0.0#cancel-timer
    case "bpmn-cancel-timer":
      return xrpc("ai.gftd.bpmn.cancelTimer", entry.payload);
    // magatama:bpmn/bpmn@1.0.0#claim-task
    case "bpmn-claim-task":
      return xrpc("ai.gftd.bpmn.claimTask", entry.payload);
    // magatama:bpmn/bpmn@1.0.0#correlate-message
    case "bpmn-correlate-message":
      return xrpc("ai.gftd.bpmn.correlateMessage", entry.payload);
    // magatama:bpmn/bpmn@1.0.0#create-timer
    case "bpmn-create-timer":
      return xrpc("ai.gftd.bpmn.createTimer", entry.payload);
    // magatama:bpmn/bpmn@1.0.0#delegate-task
    case "bpmn-delegate-task":
      return xrpc("ai.gftd.bpmn.delegateTask", entry.payload);
    // magatama:bpmn/bpmn@1.0.0#delete-definition
    case "bpmn-delete-definition":
      return xrpc("ai.gftd.bpmn.deleteDefinition", entry.payload);
    // magatama:bpmn/bpmn@1.0.0#delete-variable
    case "bpmn-delete-variable":
      return xrpc("ai.gftd.bpmn.deleteVariable", entry.payload);
    // magatama:bpmn/bpmn@1.0.0#export-xml
    case "bpmn-export-xml":
      return xrpc("ai.gftd.bpmn.exportXml", entry.payload);
    // magatama:bpmn/bpmn@1.0.0#migrate
    case "bpmn-migrate":
      return xrpc("ai.gftd.bpmn.migrate", entry.payload);
    // magatama:bpmn/bpmn@1.0.0#modify
    case "bpmn-modify":
      return xrpc("ai.gftd.bpmn.modify", entry.payload);
    // magatama:bpmn/bpmn@1.0.0#publish-message
    case "bpmn-publish-message":
      return xrpc("ai.gftd.bpmn.publishMessage", entry.payload);
    // magatama:bpmn/bpmn@1.0.0#resolve-incident
    case "bpmn-resolve-incident":
      return xrpc("ai.gftd.bpmn.resolveIncident", entry.payload);
    // magatama:bpmn/bpmn@1.0.0#resume
    case "bpmn-resume":
      return xrpc("ai.gftd.bpmn.resume", entry.payload);
    // magatama:bpmn/bpmn@1.0.0#set-element-variables
    case "bpmn-set-element-variables":
      return xrpc("ai.gftd.bpmn.setElementVariables", entry.payload);
    // magatama:bpmn/bpmn@1.0.0#set-task-due-date
    case "bpmn-set-task-due-date":
      return xrpc("ai.gftd.bpmn.setTaskDueDate", entry.payload);
    // magatama:bpmn/bpmn@1.0.0#set-task-priority
    case "bpmn-set-task-priority":
      return xrpc("ai.gftd.bpmn.setTaskPriority", entry.payload);
    // magatama:bpmn/bpmn@1.0.0#set-variables
    case "bpmn-set-variables":
      return xrpc("ai.gftd.bpmn.setVariables", entry.payload);
    // magatama:bpmn/bpmn@1.0.0#signal-instance
    case "bpmn-signal-instance":
      return xrpc("ai.gftd.bpmn.signalInstance", entry.payload);
    // magatama:bpmn/bpmn@1.0.0#suspend
    case "bpmn-suspend":
      return xrpc("ai.gftd.bpmn.suspend", entry.payload);
    // magatama:bpmn/bpmn@1.0.0#terminate
    case "bpmn-terminate":
      return xrpc("ai.gftd.bpmn.terminate", entry.payload);
    // magatama:bpmn/bpmn@1.0.0#trigger-compensation
    case "bpmn-trigger-compensation":
      return xrpc("ai.gftd.bpmn.triggerCompensation", entry.payload);
    // magatama:bpmn/bpmn@1.0.0#trigger-error
    case "bpmn-trigger-error":
      return xrpc("ai.gftd.bpmn.triggerError", entry.payload);
    // magatama:bpmn/bpmn@1.0.0#trigger-escalation
    case "bpmn-trigger-escalation":
      return xrpc("ai.gftd.bpmn.triggerEscalation", entry.payload);
    // magatama:bpmn/bpmn@1.0.0#unclaim-task
    case "bpmn-unclaim-task":
      return xrpc("ai.gftd.bpmn.unclaimTask", entry.payload);
    // magatama:bpmn/bpmn@1.0.0#update-retries
    case "bpmn-update-retries":
      return xrpc("ai.gftd.bpmn.updateRetries", entry.payload);

    // ── magatama:identity/capability@1.0.0 ──
    // magatama:identity/capability@1.0.0#add-dependency
    case "capability-add-dependency":
      return xrpc("ai.gftd.identity.addDependency", entry.payload);
    // magatama:identity/capability@1.0.0#check
    case "capability-check":
      return xrpc("ai.gftd.identity.check", entry.payload);
    // magatama:identity/capability@1.0.0#declare
    case "capability-declare":
      return xrpc("ai.gftd.identity.declare", entry.payload);
    // magatama:identity/capability@1.0.0#register
    case "capability-register":
      return xrpc("ai.gftd.identity.register", entry.payload);
    // magatama:identity/capability@1.0.0#remove
    case "capability-remove":
      return xrpc("ai.gftd.identity.remove", entry.payload);
    // magatama:identity/capability@1.0.0#remove-dependency
    case "capability-remove-dependency":
      return xrpc("ai.gftd.identity.removeDependency", entry.payload);
    // magatama:identity/capability@1.0.0#resolve
    case "capability-resolve":
      return xrpc("ai.gftd.identity.resolve", entry.payload);
    // magatama:identity/capability@1.0.0#resolve-address
    case "capability-resolve-address":
      return xrpc("ai.gftd.identity.resolveAddress", entry.payload);
    // magatama:identity/capability@1.0.0#revoke
    case "capability-revoke":
      return xrpc("ai.gftd.identity.revoke", entry.payload);

    // ── magatama:storage/cdn@1.0.0 ──
    // magatama:storage/cdn@1.0.0#delete
    case "cdn-delete":
      return xrpc("ai.gftd.storage.delete", entry.payload);
    // magatama:storage/cdn@1.0.0#delete-object
    case "cdn-delete-object":
      return xrpc("ai.gftd.storage.deleteObject", entry.payload);
    // magatama:storage/cdn@1.0.0#fetch-upload
    case "cdn-fetch-upload":
      return xrpc("ai.gftd.storage.fetchUpload", entry.payload);
    // magatama:storage/cdn@1.0.0#gateway-url
    case "cdn-gateway-url":
      return xrpc("ai.gftd.storage.gatewayUrl", entry.payload);
    // magatama:storage/cdn@1.0.0#public-url
    case "cdn-public-url":
      return xrpc("ai.gftd.storage.publicUrl", entry.payload);
    // magatama:storage/cdn@1.0.0#publish
    case "cdn-publish":
      return xrpc("ai.gftd.storage.publish", entry.payload);
    // magatama:storage/cdn@1.0.0#publish-url
    case "cdn-publish-url":
      return xrpc("ai.gftd.storage.publishUrl", entry.payload);
    // magatama:storage/cdn@1.0.0#put
    case "cdn-put":
      return xrpc("ai.gftd.storage.put", entry.payload);
    // magatama:storage/cdn@1.0.0#put-object
    case "cdn-put-object":
      return xrpc("ai.gftd.storage.putObject", entry.payload);
    // magatama:storage/cdn@1.0.0#upload
    case "cdn-upload":
      return xrpc("ai.gftd.storage.upload", entry.payload);
    // magatama:storage/cdn@1.0.0#upload-image
    case "cdn-upload-image":
      return xrpc("ai.gftd.storage.uploadImage", entry.payload);

    // ── tools-ozone:communication/communication@1.0.0 ──
    // tools-ozone:communication/communication@1.0.0#ozone-create-template
    case "communication-ozone-create-template":
      return xrpc("ai.gftd.apps.communication.ozoneCreateTemplate", entry.payload);
    // tools-ozone:communication/communication@1.0.0#ozone-delete-template
    case "communication-ozone-delete-template":
      return xrpc("ai.gftd.apps.communication.ozoneDeleteTemplate", entry.payload);
    // tools-ozone:communication/communication@1.0.0#ozone-list-templates
    case "communication-ozone-list-templates":
      return xrpc("ai.gftd.apps.communication.ozoneListTemplates", entry.payload);
    // tools-ozone:communication/communication@1.0.0#ozone-update-template
    case "communication-ozone-update-template":
      return xrpc("ai.gftd.apps.communication.ozoneUpdateTemplate", entry.payload);

    // ── magatama:core/config@1.0.0 ──
    // magatama:core/config@1.0.0#append
    case "config-append":
      return xrpc("ai.gftd.core.append", entry.payload);
    // magatama:core/config@1.0.0#get
    case "config-get":
      return xrpc("ai.gftd.core.get", entry.payload);
    // magatama:core/config@1.0.0#handle
    case "config-handle":
      return xrpc("ai.gftd.core.handle", entry.payload);
    // magatama:core/config@1.0.0#send
    case "config-send":
      return xrpc("ai.gftd.core.send", entry.payload);

    // ── magatama:consent/consent@1.0.0 ──
    // magatama:consent/consent@1.0.0#assign-clearance
    case "consent-assign-clearance":
      return xrpc("ai.gftd.consent.assignClearance", entry.payload);
    // ai-gftd:consent/consent@1.0.0#request-consent
    case "consent-request-consent":
      return xrpc("ai.gftd.apps.consent.requestConsent", entry.payload);
    // ai-gftd:consent/consent@1.0.0#resolve-consent
    case "consent-resolve-consent":
      return xrpc("ai.gftd.apps.consent.resolveConsent", entry.payload);
    // magatama:consent/consent@1.0.0#revoke-clearance
    case "consent-revoke-clearance":
      return xrpc("ai.gftd.consent.revokeClearance", entry.payload);
    // ai-gftd:consent/consent@1.0.0#revoke-consent
    case "consent-revoke-consent":
      return xrpc("ai.gftd.apps.consent.revokeConsent", entry.payload);

    // ── app-bsky:contact/contact@1.0.0 ──
    // app-bsky:contact/contact@1.0.0#dismiss-match
    case "contact-dismiss-match":
      return xrpc("ai.gftd.apps.contact.dismissMatch", entry.payload);
    // app-bsky:contact/contact@1.0.0#import-contacts
    case "contact-import-contacts":
      return xrpc("ai.gftd.apps.contact.importContacts", entry.payload);
    // app-bsky:contact/contact@1.0.0#remove-data
    case "contact-remove-data":
      return xrpc("ai.gftd.apps.contact.removeData", entry.payload);
    // app-bsky:contact/contact@1.0.0#send-notification
    case "contact-send-notification":
      return xrpc("ai.gftd.apps.contact.sendNotification", entry.payload);
    // app-bsky:contact/contact@1.0.0#start-phone-verification
    case "contact-start-phone-verification":
      return xrpc("ai.gftd.apps.contact.startPhoneVerification", entry.payload);
    // app-bsky:contact/contact@1.0.0#verify-phone
    case "contact-verify-phone":
      return xrpc("ai.gftd.apps.contact.verifyPhone", entry.payload);

    // ── chat-bsky:convo/convo@1.0.0 ──
    // chat-bsky:convo/convo@1.0.0#accept-convo
    case "convo-accept-convo":
      return xrpc("ai.gftd.apps.convo.acceptConvo", entry.payload);
    // chat-bsky:convo/convo@1.0.0#add-reaction
    case "convo-add-reaction":
      return xrpc("ai.gftd.apps.convo.addReaction", entry.payload);
    // ai-gftd:convo/convo@1.0.0#archive-convo
    case "convo-archive-convo":
      return xrpc("ai.gftd.apps.convo.archiveConvo", entry.payload);
    // ai-gftd:convo/convo@1.0.0#create-channel
    case "convo-create-channel":
      return xrpc("ai.gftd.apps.convo.createChannel", entry.payload);
    // ai-gftd:convo/convo@1.0.0#create-convo
    case "convo-create-convo":
      return xrpc("ai.gftd.apps.convo.createConvo", entry.payload);
    // ai-gftd:convo/convo@1.0.0#create-dm
    case "convo-create-dm":
      return xrpc("ai.gftd.apps.convo.createDm", entry.payload);
    // ai-gftd:convo/convo@1.0.0#create-session
    case "convo-create-session":
      return xrpc("ai.gftd.apps.convo.createSession", entry.payload);
    // chat-bsky:convo/convo@1.0.0#delete-message-for-self
    case "convo-delete-message-for-self":
      return xrpc("ai.gftd.apps.convo.deleteMessageForSelf", entry.payload);
    // ai-gftd:convo/convo@1.0.0#diff
    case "convo-diff":
      return xrpc("ai.gftd.apps.convo.diff", entry.payload);
    // ai-gftd:convo/convo@1.0.0#edit-message
    case "convo-edit-message":
      return xrpc("ai.gftd.apps.convo.editMessage", entry.payload);
    // ai-gftd:convo/convo@1.0.0#fetch-blocks
    case "convo-fetch-blocks":
      return xrpc("ai.gftd.apps.convo.fetchBlocks", entry.payload);
    // ai-gftd:convo/convo@1.0.0#invite-convo-member
    case "convo-invite-convo-member":
      return xrpc("ai.gftd.apps.convo.inviteConvoMember", entry.payload);
    // ai-gftd:convo/convo@1.0.0#join-convo
    case "convo-join-convo":
      return xrpc("ai.gftd.apps.convo.joinConvo", entry.payload);
    // ai-gftd:convo/convo@1.0.0#leave-convo
    case "convo-leave-convo":
      return xrpc("ai.gftd.apps.convo.leaveConvo", entry.payload);
    // ai-gftd:convo/convo@1.0.0#mark-read
    case "convo-mark-read":
      return xrpc("ai.gftd.apps.convo.markRead", entry.payload);
    // chat-bsky:convo/convo@1.0.0#mute-convo
    case "convo-mute-convo":
      return xrpc("ai.gftd.apps.convo.muteConvo", entry.payload);
    // ai-gftd:projector/projector@1.0.0#add-convo-member
    case "projector-add-convo-member":
      return xrpc("ai.gftd.projector.addConvoMember", entry.payload);
    // ai-gftd:projector/projector@1.0.0#add-convo-task
    case "projector-add-convo-task":
      return xrpc("ai.gftd.projector.addConvoTask", entry.payload);
    // ai-gftd:projector/projector@1.0.0#archive-project-convo
    case "projector-archive-project-convo":
      return xrpc("ai.gftd.projector.archiveProjectConvo", entry.payload);
    // ai-gftd:projector/projector@1.0.0#complete-convo-task
    case "projector-complete-convo-task":
      return xrpc("ai.gftd.projector.completeConvoTask", entry.payload);
    // ai-gftd:projector/projector@1.0.0#new-project-convo
    case "projector-new-project-convo":
      return xrpc("ai.gftd.projector.newProjectConvo", entry.payload);
    // ai-gftd:projector/projector@1.0.0#send-project-message
    case "projector-send-project-message":
      return xrpc("ai.gftd.projector.sendProjectMessage", entry.payload);
    // ai-gftd:projector/projector@1.0.0#update-project-convo
    case "projector-update-project-convo":
      return xrpc("ai.gftd.projector.updateProjectConvo", entry.payload);
    // ai-gftd:convo/convo@1.0.0#react
    case "convo-react":
      return xrpc("ai.gftd.apps.convo.react", entry.payload);
    // ai-gftd:convo/convo@1.0.0#redact-message
    case "convo-redact-message":
      return xrpc("ai.gftd.apps.convo.redactMessage", entry.payload);
    // chat-bsky:convo/convo@1.0.0#remove-reaction
    case "convo-remove-reaction":
      return xrpc("ai.gftd.apps.convo.removeReaction", entry.payload);
    // ai-gftd:convo/convo@1.0.0#search
    case "convo-search":
      return xrpc("ai.gftd.apps.convo.search", entry.payload);
    // ai-gftd:convo/convo@1.0.0#send
    case "convo-send":
      return xrpc("ai.gftd.apps.convo.send", entry.payload);
    // ai-gftd:convo/convo@1.0.0#send-message
    case "convo-send-message":
      return xrpc("ai.gftd.apps.convo.sendMessage", entry.payload);
    // chat-bsky:convo/convo@1.0.0#send-message-batch
    case "convo-send-message-batch":
      return xrpc("ai.gftd.apps.convo.sendMessageBatch", entry.payload);
    // ai-gftd:convo/convo@1.0.0#send-session-message
    case "convo-send-session-message":
      return xrpc("ai.gftd.apps.convo.sendSessionMessage", entry.payload);
    // ai-gftd:convo/convo@1.0.0#send-typing
    case "convo-send-typing":
      return xrpc("ai.gftd.apps.convo.sendTyping", entry.payload);
    // ai-gftd:convo/convo@1.0.0#set-convo-encryption
    case "convo-set-convo-encryption":
      return xrpc("ai.gftd.apps.convo.setConvoEncryption", entry.payload);
    // ai-gftd:convo/convo@1.0.0#set-profile
    case "convo-set-profile":
      return xrpc("ai.gftd.apps.convo.setProfile", entry.payload);
    // chat-bsky:convo/convo@1.0.0#unmute-convo
    case "convo-unmute-convo":
      return xrpc("ai.gftd.apps.convo.unmuteConvo", entry.payload);
    // ai-gftd:convo/convo@1.0.0#unreact
    case "convo-unreact":
      return xrpc("ai.gftd.apps.convo.unreact", entry.payload);
    // chat-bsky:convo/convo@1.0.0#update-all-read
    case "convo-update-all-read":
      return xrpc("ai.gftd.apps.convo.updateAllRead", entry.payload);
    // ai-gftd:convo/convo@1.0.0#update-convo
    case "convo-update-convo":
      return xrpc("ai.gftd.apps.convo.updateConvo", entry.payload);
    // ai-gftd:convo/convo@1.0.0#update-convo-member-role
    case "convo-update-convo-member-role":
      return xrpc("ai.gftd.apps.convo.updateConvoMemberRole", entry.payload);
    // ai-gftd:convo/convo@1.0.0#update-presence
    case "convo-update-presence":
      return xrpc("ai.gftd.apps.convo.updatePresence", entry.payload);
    // chat-bsky:convo/convo@1.0.0#update-read
    case "convo-update-read":
      return xrpc("ai.gftd.apps.convo.updateRead", entry.payload);

    // ── magatama:graph/sql@1.0.0 ──
    // magatama:graph/sql@1.0.0#batch-exec
    case "sql-batch-exec":
      return xrpc("ai.gftd.kagami.sql", entry.payload);
    // magatama:graph/sql@1.0.0#create-index
    case "sql-create-index":
      return xrpc("ai.gftd.kagami.sql", entry.payload);
    // magatama:graph/sql@1.0.0#query
    case "sql-query":
      return xrpc("ai.gftd.kagami.sql", entry.payload);
    // magatama:graph/sql@1.0.0#search
    case "sql-search":
      return xrpc("ai.gftd.kagami.sql", entry.payload);
    // magatama:graph/sql@1.0.0#write
    case "sql-write":
      return xrpc("ai.gftd.kagami.sql", entry.payload);

    // ── magatama:cloudflare/d1@1.0.0 ──
    // magatama:cloudflare/d1@1.0.0#accept-websocket
    case "d1-accept-websocket":
      return xrpc("ai.gftd.cloudflare.acceptWebsocket", entry.payload);
    // magatama:cloudflare/d1@1.0.0#block-concurrency-while
    case "d1-block-concurrency-while":
      return xrpc("ai.gftd.cloudflare.blockConcurrencyWhile", entry.payload);
    // magatama:cloudflare/d1@1.0.0#close
    case "d1-close":
      return xrpc("ai.gftd.cloudflare.close", entry.payload);
    // magatama:cloudflare/d1@1.0.0#connect
    case "d1-connect":
      return xrpc("ai.gftd.cloudflare.connect", entry.payload);
    // magatama:cloudflare/d1@1.0.0#database-size
    case "d1-database-size":
      return xrpc("ai.gftd.cloudflare.databaseSize", entry.payload);
    // magatama:cloudflare/d1@1.0.0#delete
    case "d1-delete":
      return xrpc("ai.gftd.cloudflare.delete", entry.payload);
    // magatama:cloudflare/d1@1.0.0#delete-alarm
    case "d1-delete-alarm":
      return xrpc("ai.gftd.cloudflare.deleteAlarm", entry.payload);
    // magatama:cloudflare/d1@1.0.0#delete-all
    case "d1-delete-all":
      return xrpc("ai.gftd.cloudflare.deleteAll", entry.payload);
    // magatama:cloudflare/d1@1.0.0#delete-multiple
    case "d1-delete-multiple":
      return xrpc("ai.gftd.cloudflare.deleteMultiple", entry.payload);
    // magatama:cloudflare/d1@1.0.0#dump
    case "d1-dump":
      return xrpc("ai.gftd.cloudflare.dump", entry.payload);
    // magatama:cloudflare/d1@1.0.0#exec
    case "d1-exec":
      return xrpc("ai.gftd.cloudflare.exec", entry.payload);
    // magatama:cloudflare/d1@1.0.0#fetch
    case "d1-fetch":
      return xrpc("ai.gftd.cloudflare.fetch", entry.payload);
    // magatama:cloudflare/d1@1.0.0#get
    case "d1-get":
      return xrpc("ai.gftd.cloudflare.get", entry.payload);
    // magatama:cloudflare/d1@1.0.0#id-from-name
    case "d1-id-from-name":
      return xrpc("ai.gftd.cloudflare.idFromName", entry.payload);
    // magatama:cloudflare/d1@1.0.0#new-unique-id
    case "d1-new-unique-id":
      return xrpc("ai.gftd.cloudflare.newUniqueId", entry.payload);
    // magatama:cloudflare/d1@1.0.0#put
    case "d1-put":
      return xrpc("ai.gftd.cloudflare.put", entry.payload);
    // magatama:cloudflare/d1@1.0.0#put-multiple
    case "d1-put-multiple":
      return xrpc("ai.gftd.cloudflare.putMultiple", entry.payload);
    // magatama:cloudflare/d1@1.0.0#send-binary
    case "d1-send-binary":
      return xrpc("ai.gftd.cloudflare.sendBinary", entry.payload);
    // magatama:cloudflare/d1@1.0.0#send-text
    case "d1-send-text":
      return xrpc("ai.gftd.cloudflare.sendText", entry.payload);
    // magatama:cloudflare/d1@1.0.0#set-alarm
    case "d1-set-alarm":
      return xrpc("ai.gftd.cloudflare.setAlarm", entry.payload);
    // magatama:cloudflare/d1@1.0.0#set-auto-response
    case "d1-set-auto-response":
      return xrpc("ai.gftd.cloudflare.setAutoResponse", entry.payload);
    // magatama:cloudflare/d1@1.0.0#sync
    case "d1-sync":
      return xrpc("ai.gftd.cloudflare.sync", entry.payload);
    // magatama:cloudflare/d1@1.0.0#transaction
    case "d1-transaction":
      return xrpc("ai.gftd.cloudflare.transaction", entry.payload);
    // magatama:cloudflare/d1@1.0.0#wait-until
    case "d1-wait-until":
      return xrpc("ai.gftd.cloudflare.waitUntil", entry.payload);

    // ── magatama:identity/dependency@1.0.0 ──
    // magatama:identity/dependency@1.0.0#check
    case "dependency-check":
      return xrpc("ai.gftd.identity.check", entry.payload);
    // magatama:identity/dependency@1.0.0#remove
    case "dependency-remove":
      return xrpc("ai.gftd.identity.remove", entry.payload);

    // ── magatama:dmn/dmn@1.0.0 ──
    // magatama:dmn/dmn@1.0.0#delete-model
    case "dmn-delete-model":
      return xrpc("ai.gftd.dmn.deleteModel", entry.payload);
    // magatama:dmn/dmn@1.0.0#evaluate-feel
    case "dmn-evaluate-feel":
      return xrpc("ai.gftd.dmn.evaluateFeel", entry.payload);
    // magatama:dmn/dmn@1.0.0#export-xml
    case "dmn-export-xml":
      return xrpc("ai.gftd.dmn.exportXml", entry.payload);
    // magatama:dmn/dmn@1.0.0#test-unary
    case "dmn-test-unary":
      return xrpc("ai.gftd.dmn.testUnary", entry.payload);
    // magatama:dmn/dmn@1.0.0#validate-feel
    case "dmn-validate-feel":
      return xrpc("ai.gftd.dmn.validateFeel", entry.payload);

    // ── magatama:div/documents@1.0.0 ──
    // magatama:div/documents@1.0.0#delete
    case "documents-delete":
      return xrpc("ai.gftd.div.delete", entry.payload);
    // magatama:div/documents@1.0.0#query
    case "documents-query":
      return xrpc("ai.gftd.div.query", entry.payload);
    // magatama:div/documents@1.0.0#store
    case "documents-store":
      return xrpc("ai.gftd.div.store", entry.payload);
    // magatama:div/documents@1.0.0#store-batch
    case "documents-store-batch":
      return xrpc("ai.gftd.div.storeBatch", entry.payload);

    // ── app-bsky:draft/draft@1.0.0 ──
    // app-bsky:draft/draft@1.0.0#create-draft
    case "draft-create-draft":
      return xrpc("ai.gftd.apps.draft.createDraft", entry.payload);
    // app-bsky:draft/draft@1.0.0#delete-draft
    case "draft-delete-draft":
      return xrpc("ai.gftd.apps.draft.deleteDraft", entry.payload);
    // app-bsky:draft/draft@1.0.0#update-draft
    case "draft-update-draft":
      return xrpc("ai.gftd.apps.draft.updateDraft", entry.payload);

    // ── app-bsky:feed/feed@1.0.0 ──
    // app-bsky:feed/feed@1.0.0#remove-threadgate
    case "feed-remove-threadgate":
      return xrpc("ai.gftd.apps.feed.removeThreadgate", entry.payload);
    // app-bsky:feed/feed@1.0.0#send-interactions
    case "feed-send-interactions":
      return xrpc("ai.gftd.apps.feed.sendInteractions", entry.payload);
    // app-bsky:feed/feed@1.0.0#set-threadgate
    case "feed-set-threadgate":
      return xrpc("ai.gftd.apps.feed.setThreadgate", entry.payload);
    // app-bsky:feed/feed@1.0.0#unlike-post
    case "feed-unlike-post":
      return xrpc("ai.gftd.apps.feed.unlikePost", entry.payload);
    // app-bsky:feed/feed@1.0.0#unrepost
    case "feed-unrepost":
      return xrpc("ai.gftd.apps.feed.unrepost", entry.payload);

    // ── magatama:forms/forms@1.0.0 ──
    // magatama:forms/forms@1.0.0#create-form
    case "forms-create-form":
      return xrpc("ai.gftd.forms.createForm", entry.payload);
    // magatama:forms/forms@1.0.0#delete-form
    case "forms-delete-form":
      return xrpc("ai.gftd.forms.deleteForm", entry.payload);
    // magatama:forms/forms@1.0.0#evaluate-expression
    case "forms-evaluate-expression":
      return xrpc("ai.gftd.forms.evaluateExpression", entry.payload);
    // magatama:forms/forms@1.0.0#submit-form
    case "forms-submit-form":
      return xrpc("ai.gftd.forms.submitForm", entry.payload);
    // magatama:forms/forms@1.0.0#update-form
    case "forms-update-form":
      return xrpc("ai.gftd.forms.updateForm", entry.payload);
    // magatama:forms/forms@1.0.0#validate-form
    case "forms-validate-form":
      return xrpc("ai.gftd.forms.validateForm", entry.payload);

    // ── magatama:governance/governance@1.0.0 ──
    // magatama:governance/governance@1.0.0#activities-for-function
    case "governance-activities-for-function":
      return xrpc("ai.gftd.governance.activitiesForFunction", entry.payload);
    // magatama:governance/governance@1.0.0#assign-role
    case "governance-assign-role":
      return xrpc("ai.gftd.governance.assignRole", entry.payload);
    // magatama:governance/governance@1.0.0#classify-data
    case "governance-classify-data":
      return xrpc("ai.gftd.governance.classifyData", entry.payload);
    // magatama:governance/governance@1.0.0#declare-entity
    case "governance-declare-entity":
      return xrpc("ai.gftd.governance.declareEntity", entry.payload);
    // magatama:governance/governance@1.0.0#declare-field
    case "governance-declare-field":
      return xrpc("ai.gftd.governance.declareField", entry.payload);
    // magatama:governance/governance@1.0.0#declare-risk
    case "governance-declare-risk":
      return xrpc("ai.gftd.governance.declareRisk", entry.payload);
    // magatama:governance/governance@1.0.0#declare-standard
    case "governance-declare-standard":
      return xrpc("ai.gftd.governance.declareStandard", entry.payload);
    // magatama:governance/governance@1.0.0#declare-vendor
    case "governance-declare-vendor":
      return xrpc("ai.gftd.governance.declareVendor", entry.payload);
    // magatama:governance/governance@1.0.0#define-role
    case "governance-define-role":
      return xrpc("ai.gftd.governance.defineRole", entry.payload);
    // magatama:governance/governance@1.0.0#functions-for-activity
    case "governance-functions-for-activity":
      return xrpc("ai.gftd.governance.functionsForActivity", entry.payload);
    // magatama:governance/governance@1.0.0#register
    case "governance-register":
      return xrpc("ai.gftd.governance.register", entry.payload);
    // magatama:governance/governance@1.0.0#register-manifest
    case "governance-register-manifest":
      return xrpc("ai.gftd.governance.registerManifest", entry.payload);
    // ai-gftd:governance/governance@1.0.0#register-method-policy
    case "governance-register-method-policy":
      return xrpc("ai.gftd.apps.governance.registerMethodPolicy", entry.payload);
    // ai-gftd:governance/governance@1.0.0#register-policy
    case "governance-register-policy":
      return xrpc("ai.gftd.apps.governance.registerPolicy", entry.payload);
    // magatama:governance/governance@1.0.0#remove
    case "governance-remove":
      return xrpc("ai.gftd.governance.remove", entry.payload);
    // magatama:governance/governance@1.0.0#remove-risk
    case "governance-remove-risk":
      return xrpc("ai.gftd.governance.removeRisk", entry.payload);
    // magatama:governance/governance@1.0.0#remove-role
    case "governance-remove-role":
      return xrpc("ai.gftd.governance.removeRole", entry.payload);
    // magatama:governance/governance@1.0.0#remove-vendor
    case "governance-remove-vendor":
      return xrpc("ai.gftd.governance.removeVendor", entry.payload);
    // ai-gftd:governance/governance@1.0.0#resolve-actor-visibility
    case "governance-resolve-actor-visibility":
      return xrpc("ai.gftd.apps.governance.resolveActorVisibility", entry.payload);
    // magatama:governance/governance@1.0.0#revoke-role
    case "governance-revoke-role":
      return xrpc("ai.gftd.governance.revokeRole", entry.payload);
    // ai-gftd:governance/governance@1.0.0#set-actor-sensitivity
    case "governance-set-actor-sensitivity":
      return xrpc("ai.gftd.apps.governance.setActorSensitivity", entry.payload);

    // ── app-bsky:graph/graph@1.0.0 ──
    // app-bsky:graph/graph@1.0.0#ack-feed
    case "graph-ack-feed":
      return xrpc("ai.gftd.apps.graph.ackFeed", entry.payload);
    // app-bsky:graph/graph@1.0.0#approve-all-follow-requests
    case "graph-approve-all-follow-requests":
      return xrpc("ai.gftd.apps.graph.approveAllFollowRequests", entry.payload);
    // app-bsky:graph/graph@1.0.0#approve-follow-request
    case "graph-approve-follow-request":
      return xrpc("ai.gftd.apps.graph.approveFollowRequest", entry.payload);
    // app-bsky:graph/graph@1.0.0#block-actor
    case "graph-block-actor":
      return xrpc("ai.gftd.apps.graph.blockActor", entry.payload);
    // app-bsky:graph/graph@1.0.0#follow
    case "graph-follow":
      return xrpc("ai.gftd.apps.graph.follow", entry.payload);
    // app-bsky:graph/graph@1.0.0#leaderboard
    case "graph-leaderboard":
      return xrpc("ai.gftd.apps.graph.leaderboard", entry.payload);
    // app-bsky:graph/graph@1.0.0#mute-actor
    case "graph-mute-actor":
      return xrpc("ai.gftd.apps.graph.muteActor", entry.payload);
    // app-bsky:graph/graph@1.0.0#mute-actor-list
    case "graph-mute-actor-list":
      return xrpc("ai.gftd.apps.graph.muteActorList", entry.payload);
    // app-bsky:graph/graph@1.0.0#mute-thread
    case "graph-mute-thread":
      return xrpc("ai.gftd.apps.graph.muteThread", entry.payload);
    // app-bsky:graph/graph@1.0.0#pull-feed
    case "graph-pull-feed":
      return xrpc("ai.gftd.apps.graph.pullFeed", entry.payload);
    // app-bsky:graph/graph@1.0.0#reject-follow-request
    case "graph-reject-follow-request":
      return xrpc("ai.gftd.apps.graph.rejectFollowRequest", entry.payload);
    // app-bsky:graph/graph@1.0.0#unblock-actor
    case "graph-unblock-actor":
      return xrpc("ai.gftd.apps.graph.unblockActor", entry.payload);
    // app-bsky:graph/graph@1.0.0#unfollow
    case "graph-unfollow":
      return xrpc("ai.gftd.apps.graph.unfollow", entry.payload);
    // app-bsky:graph/graph@1.0.0#unfollow-user
    case "graph-unfollow-user":
      return xrpc("ai.gftd.apps.graph.unfollowUser", entry.payload);
    // app-bsky:graph/graph@1.0.0#unmute-actor
    case "graph-unmute-actor":
      return xrpc("ai.gftd.apps.graph.unmuteActor", entry.payload);
    // app-bsky:graph/graph@1.0.0#unmute-actor-list
    case "graph-unmute-actor-list":
      return xrpc("ai.gftd.apps.graph.unmuteActorList", entry.payload);
    // app-bsky:graph/graph@1.0.0#unmute-thread
    case "graph-unmute-thread":
      return xrpc("ai.gftd.apps.graph.unmuteThread", entry.payload);

    // ── tools-ozone:hosting/hosting@1.0.0 ──
    // tools-ozone:hosting/hosting@1.0.0#ozone-get-account-history
    case "hosting-ozone-get-account-history":
      return xrpc("ai.gftd.apps.hosting.ozoneGetAccountHistory", entry.payload);

    // ── com-atproto:identity/identity@1.0.0 ──
    // com-atproto:identity/identity@1.0.0#create
    case "identity-create":
      return xrpc("ai.gftd.apps.identity.create", entry.payload);
    // com-atproto:identity/identity@1.0.0#create-record
    case "identity-create-record":
      return xrpc("ai.gftd.apps.identity.createRecord", entry.payload);
    // com-atproto:identity/identity@1.0.0#deactivate
    case "identity-deactivate":
      return xrpc("ai.gftd.apps.identity.deactivate", entry.payload);
    // com-atproto:identity/identity@1.0.0#delete-record
    case "identity-delete-record":
      return xrpc("ai.gftd.apps.identity.deleteRecord", entry.payload);
    // com-atproto:identity/identity@1.0.0#refresh-identity
    case "identity-refresh-identity":
      return xrpc("ai.gftd.apps.identity.refreshIdentity", entry.payload);
    // magatama:identity/identity@1.0.0#register
    case "identity-register":
      return xrpc("ai.gftd.identity.register", entry.payload);
    // com-atproto:identity/identity@1.0.0#request-plc-operation-signature
    case "identity-request-plc-operation-signature":
      return xrpc("ai.gftd.apps.identity.requestPlcOperationSignature", entry.payload);
    // magatama:identity/identity@1.0.0#resolve
    case "identity-resolve":
      return xrpc("ai.gftd.identity.resolve", entry.payload);
    // magatama:identity/identity@1.0.0#resolve-address
    case "identity-resolve-address":
      return xrpc("ai.gftd.identity.resolveAddress", entry.payload);
    // com-atproto:identity/identity@1.0.0#resolve-did
    case "identity-resolve-did":
      return xrpc("ai.gftd.apps.identity.resolveDid", entry.payload);
    // com-atproto:identity/identity@1.0.0#resolve-handle
    case "identity-resolve-handle":
      return xrpc("ai.gftd.apps.identity.resolveHandle", entry.payload);
    // com-atproto:identity/identity@1.0.0#resolve-identity
    case "identity-resolve-identity":
      return xrpc("ai.gftd.apps.identity.resolveIdentity", entry.payload);
    // com-atproto:identity/identity@1.0.0#rotate-key
    case "identity-rotate-key":
      return xrpc("ai.gftd.apps.identity.rotateKey", entry.payload);
    // com-atproto:identity/identity@1.0.0#sign-plc-operation
    case "identity-sign-plc-operation":
      return xrpc("ai.gftd.apps.identity.signPlcOperation", entry.payload);
    // com-atproto:identity/identity@1.0.0#submit-plc-operation
    case "identity-submit-plc-operation":
      return xrpc("ai.gftd.apps.identity.submitPlcOperation", entry.payload);
    // com-atproto:identity/identity@1.0.0#update
    case "identity-update":
      return xrpc("ai.gftd.apps.identity.update", entry.payload);
    // com-atproto:identity/identity@1.0.0#update-handle
    case "identity-update-handle":
      return xrpc("ai.gftd.apps.identity.updateHandle", entry.payload);
    // com-atproto:identity/identity@1.0.0#update-record
    case "identity-update-record":
      return xrpc("ai.gftd.apps.identity.updateRecord", entry.payload);

    // ── ai-gftd:invoke/invoke@1.0.0 ──
    // ai-gftd:invoke/invoke@1.0.0#invoke
    case "invoke-invoke":
      return xrpc("ai.gftd.apps.invoke.invoke", entry.payload);
    // ai-gftd:invoke/invoke@1.0.0#invoke-stream
    case "invoke-invoke-stream":
      return xrpc("ai.gftd.apps.invoke.invokeStream", entry.payload);

    // ── gftd:ipfs/ipfs-gateway@1.0.0 ──
    // gftd:ipfs/ipfs-gateway@1.0.0#resolve
    case "ipfs-gateway-resolve":
      return xrpc("ai.gftd.apps.ipfs.resolve", entry.payload);

    // ── com-atproto:label/label@1.0.0 ──
    // com-atproto:label/label@1.0.0#create-label
    case "label-create-label":
      return xrpc("ai.gftd.apps.label.createLabel", entry.payload);
    // com-atproto:label/label@1.0.0#declare-labeler
    case "label-declare-labeler":
      return xrpc("ai.gftd.apps.label.declareLabeler", entry.payload);
    // com-atproto:label/label@1.0.0#set-content-pref
    case "label-set-content-pref":
      return xrpc("ai.gftd.apps.label.setContentPref", entry.payload);
    // com-atproto:label/label@1.0.0#subscribe-labels
    case "label-subscribe-labels":
      return xrpc("ai.gftd.apps.label.subscribeLabels", entry.payload);
    // com-atproto:label/label@1.0.0#unsubscribe-labeler
    case "label-unsubscribe-labeler":
      return xrpc("ai.gftd.apps.label.unsubscribeLabeler", entry.payload);

    // ── com-atproto:lexicon/lexicon@1.0.0 ──
    // com-atproto:lexicon/lexicon@1.0.0#resolve-lexicon
    case "lexicon-resolve-lexicon":
      return xrpc("ai.gftd.apps.lexicon.resolveLexicon", entry.payload);

    // ── tools-ozone:moderation/moderation@1.0.0 ──
    // tools-ozone:moderation/moderation@1.0.0#ozone-cancel-scheduled-actions
    case "moderation-ozone-cancel-scheduled-actions":
      return xrpc("ai.gftd.apps.moderation.ozoneCancelScheduledActions", entry.payload);
    // tools-ozone:moderation/moderation@1.0.0#ozone-emit-event
    case "moderation-ozone-emit-event":
      return xrpc("ai.gftd.apps.moderation.ozoneEmitEvent", entry.payload);
    // tools-ozone:moderation/moderation@1.0.0#ozone-get-account-timeline
    case "moderation-ozone-get-account-timeline":
      return xrpc("ai.gftd.apps.moderation.ozoneGetAccountTimeline", entry.payload);
    // tools-ozone:moderation/moderation@1.0.0#ozone-get-event
    case "moderation-ozone-get-event":
      return xrpc("ai.gftd.apps.moderation.ozoneGetEvent", entry.payload);
    // tools-ozone:moderation/moderation@1.0.0#ozone-get-record
    case "moderation-ozone-get-record":
      return xrpc("ai.gftd.apps.moderation.ozoneGetRecord", entry.payload);
    // tools-ozone:moderation/moderation@1.0.0#ozone-get-records
    case "moderation-ozone-get-records":
      return xrpc("ai.gftd.apps.moderation.ozoneGetRecords", entry.payload);
    // tools-ozone:moderation/moderation@1.0.0#ozone-get-repo
    case "moderation-ozone-get-repo":
      return xrpc("ai.gftd.apps.moderation.ozoneGetRepo", entry.payload);
    // tools-ozone:moderation/moderation@1.0.0#ozone-get-reporter-stats
    case "moderation-ozone-get-reporter-stats":
      return xrpc("ai.gftd.apps.moderation.ozoneGetReporterStats", entry.payload);
    // tools-ozone:moderation/moderation@1.0.0#ozone-get-repos
    case "moderation-ozone-get-repos":
      return xrpc("ai.gftd.apps.moderation.ozoneGetRepos", entry.payload);
    // tools-ozone:moderation/moderation@1.0.0#ozone-get-subjects
    case "moderation-ozone-get-subjects":
      return xrpc("ai.gftd.apps.moderation.ozoneGetSubjects", entry.payload);
    // tools-ozone:moderation/moderation@1.0.0#ozone-list-scheduled-actions
    case "moderation-ozone-list-scheduled-actions":
      return xrpc("ai.gftd.apps.moderation.ozoneListScheduledActions", entry.payload);
    // tools-ozone:moderation/moderation@1.0.0#ozone-query-events
    case "moderation-ozone-query-events":
      return xrpc("ai.gftd.apps.moderation.ozoneQueryEvents", entry.payload);
    // tools-ozone:moderation/moderation@1.0.0#ozone-query-statuses
    case "moderation-ozone-query-statuses":
      return xrpc("ai.gftd.apps.moderation.ozoneQueryStatuses", entry.payload);
    // tools-ozone:moderation/moderation@1.0.0#ozone-schedule-action
    case "moderation-ozone-schedule-action":
      return xrpc("ai.gftd.apps.moderation.ozoneScheduleAction", entry.payload);
    // tools-ozone:moderation/moderation@1.0.0#ozone-search-repos
    case "moderation-ozone-search-repos":
      return xrpc("ai.gftd.apps.moderation.ozoneSearchRepos", entry.payload);
    // com-atproto:moderation/moderation@1.0.0#report-content
    case "moderation-report-content":
      return xrpc("ai.gftd.apps.moderation.reportContent", entry.payload);
    // chat-bsky:moderation/moderation@1.0.0#update-chat-actor-access
    case "moderation-update-chat-actor-access":
      return xrpc("ai.gftd.apps.moderation.updateChatActorAccess", entry.payload);

    // ── app-bsky:notification/notification@1.0.0 ──
    // app-bsky:notification/notification@1.0.0#put-activity-subscription
    case "notification-put-activity-subscription":
      return xrpc("ai.gftd.apps.notification.putActivitySubscription", entry.payload);
    // app-bsky:notification/notification@1.0.0#put-notification-preferences
    case "notification-put-notification-preferences":
      return xrpc("ai.gftd.apps.notification.putNotificationPreferences", entry.payload);
    // app-bsky:notification/notification@1.0.0#put-notification-preferences-v2
    case "notification-put-notification-preferences-v2":
      return xrpc("ai.gftd.apps.notification.putNotificationPreferencesV2", entry.payload);
    // app-bsky:notification/notification@1.0.0#register-push
    case "notification-register-push":
      return xrpc("ai.gftd.apps.notification.registerPush", entry.payload);
    // app-bsky:notification/notification@1.0.0#unregister-push
    case "notification-unregister-push":
      return xrpc("ai.gftd.apps.notification.unregisterPush", entry.payload);
    // app-bsky:notification/notification@1.0.0#update-seen
    case "notification-update-seen":
      return xrpc("ai.gftd.apps.notification.updateSeen", entry.payload);

    // ── gftd:states/organization-directory@0.1.0 ──
    // gftd:states/organization-directory@0.1.0#receive-inter-org-message
    case "organization-directory-receive-inter-org-message":
      return xrpc("ai.gftd.apps.states.receiveInterOrgMessage", entry.payload);
    // gftd:states/organization-directory@0.1.0#send-inter-org-message
    case "organization-directory-send-inter-org-message":
      return xrpc("ai.gftd.apps.states.sendInterOrgMessage", entry.payload);
    // magatama:dm2/organization@1.0.0#register
    case "organization-register":
      return xrpc("ai.gftd.dm2.register", entry.payload);
    // magatama:dm2/organization@1.0.0#resolve
    case "organization-resolve":
      return xrpc("ai.gftd.dm2.resolve", entry.payload);
    // magatama:dm2/organization@1.0.0#resolve-lineage
    case "organization-resolve-lineage":
      return xrpc("ai.gftd.dm2.resolveLineage", entry.payload);
    // magatama:dm2/organization@1.0.0#upsert
    case "organization-upsert":
      return xrpc("ai.gftd.dm2.upsert", entry.payload);

    // ── magatama:pubsub/pubsub@1.0.0 ──
    // magatama:pubsub/pubsub@1.0.0#ack
    case "pubsub-ack":
      return xrpc("ai.gftd.pubsub.ack", entry.payload);
    // magatama:pubsub/pubsub@1.0.0#cursor
    case "pubsub-cursor":
      return xrpc("ai.gftd.pubsub.cursor", entry.payload);
    // magatama:pubsub/pubsub@1.0.0#publish
    case "pubsub-publish":
      return xrpc("ai.gftd.pubsub.publish", entry.payload);
    // magatama:pubsub/pubsub@1.0.0#pull
    case "pubsub-pull":
      return xrpc("ai.gftd.pubsub.pull", entry.payload);

    // ── magatama:coverage/query@1.0.0 ──
    // magatama:coverage/query@1.0.0#report-dimension
    case "query-report-dimension":
      return xrpc("ai.gftd.coverage.reportDimension", entry.payload);
    // magatama:coverage/query@1.0.0#report-gap
    case "query-report-gap":
      return xrpc("ai.gftd.coverage.reportGap", entry.payload);
    // magatama:coverage/query@1.0.0#scan
    case "query-scan":
      return xrpc("ai.gftd.coverage.scan", entry.payload);

    // ── com-atproto:repo/repo@1.0.0 ──
    // com-atproto:repo/repo@1.0.0#apply-writes
    case "repo-apply-writes":
      return xrpc("ai.gftd.apps.repo.applyWrites", entry.payload);
    // com-atproto:repo/repo@1.0.0#create-follow
    case "repo-create-follow":
      return xrpc("ai.gftd.apps.repo.createFollow", entry.payload);
    // com-atproto:repo/repo@1.0.0#create-like
    case "repo-create-like":
      return xrpc("ai.gftd.apps.repo.createLike", entry.payload);
    // com-atproto:repo/repo@1.0.0#create-post
    case "repo-create-post":
      return xrpc("ai.gftd.apps.repo.createPost", entry.payload);
    // com-atproto:repo/repo@1.0.0#create-record
    case "repo-create-record":
      return xrpc("ai.gftd.apps.repo.createRecord", entry.payload);
    // com-atproto:repo/repo@1.0.0#create-repost
    case "repo-create-repost":
      return xrpc("ai.gftd.apps.repo.createRepost", entry.payload);
    // com-atproto:repo/repo@1.0.0#delete-record
    case "repo-delete-record":
      return xrpc("ai.gftd.apps.repo.deleteRecord", entry.payload);
    // com-atproto:repo/repo@1.0.0#import-repo
    case "repo-import-repo":
      return xrpc("ai.gftd.apps.repo.importRepo", entry.payload);
    // com-atproto:repo/repo@1.0.0#put-profile
    case "repo-put-profile":
      return xrpc("ai.gftd.apps.repo.putProfile", entry.payload);
    // com-atproto:repo/repo@1.0.0#put-record
    case "repo-put-record":
      return xrpc("ai.gftd.apps.repo.putRecord", entry.payload);
    // com-atproto:repo/repo@1.0.0#upload-blob
    case "repo-upload-blob":
      return xrpc("ai.gftd.apps.repo.uploadBlob", entry.payload);

    // ── magatama:rpc/resilience@1.0.0 ──
    // magatama:rpc/resilience@1.0.0#record-failure
    case "resilience-record-failure":
      return xrpc("ai.gftd.rpc.recordFailure", entry.payload);
    // magatama:rpc/resilience@1.0.0#record-success
    case "resilience-record-success":
      return xrpc("ai.gftd.rpc.recordSuccess", entry.payload);
    // magatama:rpc/resilience@1.0.0#register-breaker
    case "resilience-register-breaker":
      return xrpc("ai.gftd.rpc.registerBreaker", entry.payload);
    // magatama:rpc/resilience@1.0.0#register-health-check
    case "resilience-register-health-check":
      return xrpc("ai.gftd.rpc.registerHealthCheck", entry.payload);
    // magatama:rpc/resilience@1.0.0#report-health
    case "resilience-report-health":
      return xrpc("ai.gftd.rpc.reportHealth", entry.payload);

    // ── ai-gftd:rtc/rtc@1.0.0 ──
    // ai-gftd:rtc/rtc@1.0.0#hangup-call
    case "rtc-hangup-call":
      return xrpc("ai.gftd.apps.rtc.hangupCall", entry.payload);
    // ai-gftd:rtc/rtc@1.0.0#send-call-answer
    case "rtc-send-call-answer":
      return xrpc("ai.gftd.apps.rtc.sendCallAnswer", entry.payload);
    // ai-gftd:rtc/rtc@1.0.0#send-call-ice
    case "rtc-send-call-ice":
      return xrpc("ai.gftd.apps.rtc.sendCallIce", entry.payload);
    // ai-gftd:rtc/rtc@1.0.0#send-call-offer
    case "rtc-send-call-offer":
      return xrpc("ai.gftd.apps.rtc.sendCallOffer", entry.payload);
    // ai-gftd:rtc/rtc@1.0.0#subscribe-push
    case "rtc-subscribe-push":
      return xrpc("ai.gftd.apps.rtc.subscribePush", entry.payload);
    // ai-gftd:rtc/rtc@1.0.0#unsubscribe-push
    case "rtc-unsubscribe-push":
      return xrpc("ai.gftd.apps.rtc.unsubscribePush", entry.payload);

    // ── tools-ozone:safelink/safelink@1.0.0 ──
    // tools-ozone:safelink/safelink@1.0.0#ozone-safelink-add-rule
    case "safelink-ozone-safelink-add-rule":
      return xrpc("ai.gftd.apps.safelink.ozoneSafelinkAddRule", entry.payload);
    // tools-ozone:safelink/safelink@1.0.0#ozone-safelink-query-events
    case "safelink-ozone-safelink-query-events":
      return xrpc("ai.gftd.apps.safelink.ozoneSafelinkQueryEvents", entry.payload);
    // tools-ozone:safelink/safelink@1.0.0#ozone-safelink-query-rules
    case "safelink-ozone-safelink-query-rules":
      return xrpc("ai.gftd.apps.safelink.ozoneSafelinkQueryRules", entry.payload);
    // tools-ozone:safelink/safelink@1.0.0#ozone-safelink-remove-rule
    case "safelink-ozone-safelink-remove-rule":
      return xrpc("ai.gftd.apps.safelink.ozoneSafelinkRemoveRule", entry.payload);
    // tools-ozone:safelink/safelink@1.0.0#ozone-safelink-update-rule
    case "safelink-ozone-safelink-update-rule":
      return xrpc("ai.gftd.apps.safelink.ozoneSafelinkUpdateRule", entry.payload);

    // ── magatama:secrets/secrets@1.0.0 ──
    // magatama:secrets/secrets@1.0.0#create-vault
    case "secrets-create-vault":
      return xrpc("ai.gftd.secrets.createVault", entry.payload);
    // magatama:secrets/secrets@1.0.0#delete
    case "secrets-delete":
      return xrpc("ai.gftd.secrets.delete", entry.payload);
    // magatama:secrets/secrets@1.0.0#delete-item
    case "secrets-delete-item":
      return xrpc("ai.gftd.secrets.deleteItem", entry.payload);
    // magatama:secrets/secrets@1.0.0#fetch-delegated
    case "secrets-fetch-delegated":
      return xrpc("ai.gftd.secrets.fetchDelegated", entry.payload);
    // magatama:secrets/secrets@1.0.0#get
    case "secrets-get":
      return xrpc("ai.gftd.secrets.get", entry.payload);
    // magatama:secrets/secrets@1.0.0#put-item
    case "secrets-put-item":
      return xrpc("ai.gftd.secrets.putItem", entry.payload);
    // magatama:secrets/secrets@1.0.0#remove-member
    case "secrets-remove-member":
      return xrpc("ai.gftd.secrets.removeMember", entry.payload);
    // magatama:secrets/secrets@1.0.0#revoke-delegation
    case "secrets-revoke-delegation":
      return xrpc("ai.gftd.secrets.revokeDelegation", entry.payload);
    // magatama:secrets/secrets@1.0.0#set
    case "secrets-set":
      return xrpc("ai.gftd.secrets.set", entry.payload);

    // ── ai-gftd:serve/serve@1.0.0 ──
    // ai-gftd:serve/serve@1.0.0#handle
    case "serve-handle":
      return xrpc("ai.gftd.apps.serve.handle", entry.payload);
    // ai-gftd:serve/serve@1.0.0#handle-stream
    case "serve-handle-stream":
      return xrpc("ai.gftd.apps.serve.handleStream", entry.payload);

    // ── com-atproto:server/server@1.0.0 ──
    // com-atproto:server/server@1.0.0#activate-account
    case "server-activate-account":
      return xrpc("ai.gftd.apps.server.activateAccount", entry.payload);
    // com-atproto:server/server@1.0.0#confirm-email
    case "server-confirm-email":
      return xrpc("ai.gftd.apps.server.confirmEmail", entry.payload);
    // com-atproto:server/server@1.0.0#create-account
    case "server-create-account":
      return xrpc("ai.gftd.apps.server.createAccount", entry.payload);
    // com-atproto:server/server@1.0.0#create-app-password
    case "server-create-app-password":
      return xrpc("ai.gftd.apps.server.createAppPassword", entry.payload);
    // com-atproto:server/server@1.0.0#create-invite-code
    case "server-create-invite-code":
      return xrpc("ai.gftd.apps.server.createInviteCode", entry.payload);
    // com-atproto:server/server@1.0.0#create-invite-codes
    case "server-create-invite-codes":
      return xrpc("ai.gftd.apps.server.createInviteCodes", entry.payload);
    // com-atproto:server/server@1.0.0#create-session
    case "server-create-session":
      return xrpc("ai.gftd.apps.server.createSession", entry.payload);
    // com-atproto:server/server@1.0.0#deactivate-account
    case "server-deactivate-account":
      return xrpc("ai.gftd.apps.server.deactivateAccount", entry.payload);
    // com-atproto:server/server@1.0.0#delete-account
    case "server-delete-account":
      return xrpc("ai.gftd.apps.server.deleteAccount", entry.payload);
    // com-atproto:server/server@1.0.0#delete-session
    case "server-delete-session":
      return xrpc("ai.gftd.apps.server.deleteSession", entry.payload);
    // tools-ozone:server/server@1.0.0#ozone-get-config
    case "server-ozone-get-config":
      return xrpc("ai.gftd.apps.server.ozoneGetConfig", entry.payload);
    // com-atproto:server/server@1.0.0#refresh-session
    case "server-refresh-session":
      return xrpc("ai.gftd.apps.server.refreshSession", entry.payload);
    // com-atproto:server/server@1.0.0#request-account-delete
    case "server-request-account-delete":
      return xrpc("ai.gftd.apps.server.requestAccountDelete", entry.payload);
    // com-atproto:server/server@1.0.0#request-email-confirmation
    case "server-request-email-confirmation":
      return xrpc("ai.gftd.apps.server.requestEmailConfirmation", entry.payload);
    // com-atproto:server/server@1.0.0#request-email-update
    case "server-request-email-update":
      return xrpc("ai.gftd.apps.server.requestEmailUpdate", entry.payload);
    // com-atproto:server/server@1.0.0#request-password-reset
    case "server-request-password-reset":
      return xrpc("ai.gftd.apps.server.requestPasswordReset", entry.payload);
    // com-atproto:server/server@1.0.0#reserve-signing-key
    case "server-reserve-signing-key":
      return xrpc("ai.gftd.apps.server.reserveSigningKey", entry.payload);
    // com-atproto:server/server@1.0.0#reset-password
    case "server-reset-password":
      return xrpc("ai.gftd.apps.server.resetPassword", entry.payload);
    // com-atproto:server/server@1.0.0#revoke-app-password
    case "server-revoke-app-password":
      return xrpc("ai.gftd.apps.server.revokeAppPassword", entry.payload);
    // com-atproto:server/server@1.0.0#update-email
    case "server-update-email":
      return xrpc("ai.gftd.apps.server.updateEmail", entry.payload);

    // ── tools-ozone:set/set@1.0.0 ──
    // tools-ozone:set/set@1.0.0#ozone-set-add-values
    case "set-ozone-set-add-values":
      return xrpc("ai.gftd.apps.set.ozoneSetAddValues", entry.payload);
    // tools-ozone:set/set@1.0.0#ozone-set-delete-set
    case "set-ozone-set-delete-set":
      return xrpc("ai.gftd.apps.set.ozoneSetDeleteSet", entry.payload);
    // tools-ozone:set/set@1.0.0#ozone-set-delete-values
    case "set-ozone-set-delete-values":
      return xrpc("ai.gftd.apps.set.ozoneSetDeleteValues", entry.payload);
    // tools-ozone:set/set@1.0.0#ozone-set-get-values
    case "set-ozone-set-get-values":
      return xrpc("ai.gftd.apps.set.ozoneSetGetValues", entry.payload);
    // tools-ozone:set/set@1.0.0#ozone-set-query-sets
    case "set-ozone-set-query-sets":
      return xrpc("ai.gftd.apps.set.ozoneSetQuerySets", entry.payload);
    // tools-ozone:set/set@1.0.0#ozone-set-upsert-set
    case "set-ozone-set-upsert-set":
      return xrpc("ai.gftd.apps.set.ozoneSetUpsertSet", entry.payload);

    // ── tools-ozone:setting/setting@1.0.0 ──
    // tools-ozone:setting/setting@1.0.0#ozone-setting-list-options
    case "setting-ozone-setting-list-options":
      return xrpc("ai.gftd.apps.setting.ozoneSettingListOptions", entry.payload);
    // tools-ozone:setting/setting@1.0.0#ozone-setting-remove-options
    case "setting-ozone-setting-remove-options":
      return xrpc("ai.gftd.apps.setting.ozoneSettingRemoveOptions", entry.payload);
    // tools-ozone:setting/setting@1.0.0#ozone-setting-upsert-option
    case "setting-ozone-setting-upsert-option":
      return xrpc("ai.gftd.apps.setting.ozoneSettingUpsertOption", entry.payload);

    // ── ai-gftd:magatama/shinka@1.0.0 ──
    // ai-gftd:magatama/shinka@1.0.0#on-follow-request
    case "shinka-on-follow-request":
      return xrpc("ai.gftd.apps.magatama.onFollowRequest", entry.payload);
    // ai-gftd:magatama/shinka@1.0.0#on-heartbeat
    case "shinka-on-heartbeat":
      return xrpc("ai.gftd.apps.magatama.onHeartbeat", entry.payload);
    // ai-gftd:magatama/shinka@1.0.0#on-new-follower
    case "shinka-on-new-follower":
      return xrpc("ai.gftd.apps.magatama.onNewFollower", entry.payload);
    // ai-gftd:magatama/shinka@1.0.0#on-reaction
    case "shinka-on-reaction":
      return xrpc("ai.gftd.apps.magatama.onReaction", entry.payload);

    // ── ai-gftd:signal/signal@1.0.0 ──
    // ai-gftd:signal/signal@1.0.0#build-pre-key-bundle
    case "signal-build-pre-key-bundle":
      return xrpc("ai.gftd.apps.signal.buildPreKeyBundle", entry.payload);
    // ai-gftd:signal/signal@1.0.0#generate-identity
    case "signal-generate-identity":
      return xrpc("ai.gftd.apps.signal.generateIdentity", entry.payload);
    // ai-gftd:signal/signal@1.0.0#generate-one-time-prekey
    case "signal-generate-one-time-prekey":
      return xrpc("ai.gftd.apps.signal.generateOneTimePrekey", entry.payload);
    // ai-gftd:signal/signal@1.0.0#generate-signed-prekey
    case "signal-generate-signed-prekey":
      return xrpc("ai.gftd.apps.signal.generateSignedPrekey", entry.payload);
    // ai-gftd:signal/signal@1.0.0#group-decrypt
    case "signal-group-decrypt":
      return xrpc("ai.gftd.apps.signal.groupDecrypt", entry.payload);
    // ai-gftd:signal/signal@1.0.0#group-encrypt
    case "signal-group-encrypt":
      return xrpc("ai.gftd.apps.signal.groupEncrypt", entry.payload);
    // ai-gftd:signal/signal@1.0.0#group-init-sender
    case "signal-group-init-sender":
      return xrpc("ai.gftd.apps.signal.groupInitSender", entry.payload);
    // ai-gftd:signal/signal@1.0.0#group-process-distribution
    case "signal-group-process-distribution":
      return xrpc("ai.gftd.apps.signal.groupProcessDistribution", entry.payload);
    // ai-gftd:signal/signal@1.0.0#ratchet-decrypt
    case "signal-ratchet-decrypt":
      return xrpc("ai.gftd.apps.signal.ratchetDecrypt", entry.payload);
    // ai-gftd:signal/signal@1.0.0#ratchet-encrypt
    case "signal-ratchet-encrypt":
      return xrpc("ai.gftd.apps.signal.ratchetEncrypt", entry.payload);
    // ai-gftd:signal/signal@1.0.0#ratchet-init-receiver
    case "signal-ratchet-init-receiver":
      return xrpc("ai.gftd.apps.signal.ratchetInitReceiver", entry.payload);
    // ai-gftd:signal/signal@1.0.0#ratchet-init-sender
    case "signal-ratchet-init-sender":
      return xrpc("ai.gftd.apps.signal.ratchetInitSender", entry.payload);
    // ai-gftd:signal/signal@1.0.0#x3dh-initiate
    case "signal-x3dh-initiate":
      return xrpc("ai.gftd.apps.signal.x3dhInitiate", entry.payload);
    // ai-gftd:signal/signal@1.0.0#x3dh-respond
    case "signal-x3dh-respond":
      return xrpc("ai.gftd.apps.signal.x3dhRespond", entry.payload);

    // ── tools-ozone:signature/signature@1.0.0 ──
    // tools-ozone:signature/signature@1.0.0#ozone-signature-find-correlation
    case "signature-ozone-signature-find-correlation":
      return xrpc("ai.gftd.apps.signature.ozoneSignatureFindCorrelation", entry.payload);
    // tools-ozone:signature/signature@1.0.0#ozone-signature-find-related-accounts
    case "signature-ozone-signature-find-related-accounts":
      return xrpc("ai.gftd.apps.signature.ozoneSignatureFindRelatedAccounts", entry.payload);
    // tools-ozone:signature/signature@1.0.0#ozone-signature-search-accounts
    case "signature-ozone-signature-search-accounts":
      return xrpc("ai.gftd.apps.signature.ozoneSignatureSearchAccounts", entry.payload);

    // ── magatama:identity/source@1.0.0 ──
    // magatama:identity/source@1.0.0#deactivate
    case "source-deactivate":
      return xrpc("ai.gftd.identity.deactivate", entry.payload);
    // magatama:identity/source@1.0.0#get
    case "source-get":
      return xrpc("ai.gftd.identity.get", entry.payload);
    // magatama:identity/source@1.0.0#list
    case "source-list":
      return xrpc("ai.gftd.identity.list", entry.payload);
    // magatama:identity/source@1.0.0#register
    case "source-register":
      return xrpc("ai.gftd.identity.register", entry.payload);
    // magatama:identity/source@1.0.0#update
    case "source-update":
      return xrpc("ai.gftd.identity.update", entry.payload);

    // ── ai-gftd:wrpc/stream@1.0.0 ──
    // ai-gftd:wrpc/stream@1.0.0#close
    case "stream-close":
      return xrpc("ai.gftd.apps.wrpc.close", entry.payload);

    // ── com-atproto:sync/subscribe-repos@1.0.0 ──
    // com-atproto:sync/subscribe-repos@1.0.0#handle-commit
    case "subscribe-repos-handle-commit":
      return xrpc("ai.gftd.apps.sync.handleCommit", entry.payload);

    // ── tools-ozone:team/team@1.0.0 ──
    // tools-ozone:team/team@1.0.0#ozone-team-add-member
    case "team-ozone-team-add-member":
      return xrpc("ai.gftd.apps.team.ozoneTeamAddMember", entry.payload);
    // tools-ozone:team/team@1.0.0#ozone-team-delete-member
    case "team-ozone-team-delete-member":
      return xrpc("ai.gftd.apps.team.ozoneTeamDeleteMember", entry.payload);
    // tools-ozone:team/team@1.0.0#ozone-team-list-members
    case "team-ozone-team-list-members":
      return xrpc("ai.gftd.apps.team.ozoneTeamListMembers", entry.payload);
    // tools-ozone:team/team@1.0.0#ozone-team-update-member
    case "team-ozone-team-update-member":
      return xrpc("ai.gftd.apps.team.ozoneTeamUpdateMember", entry.payload);

    // ── magatama:trust/trust-policy@1.0.0 ──
    // magatama:trust/trust-policy@1.0.0#batch-score
    case "trust-policy-batch-score":
      return xrpc("ai.gftd.trust.batchScore", entry.payload);
    // magatama:trust/trust-policy@1.0.0#declare-requirements
    case "trust-policy-declare-requirements":
      return xrpc("ai.gftd.trust.declareRequirements", entry.payload);
    // magatama:trust/trust-policy@1.0.0#detail
    case "trust-policy-detail":
      return xrpc("ai.gftd.trust.detail", entry.payload);
    // magatama:trust/trust-policy@1.0.0#history
    case "trust-policy-history":
      return xrpc("ai.gftd.trust.history", entry.payload);
    // magatama:trust/trust-policy@1.0.0#leaderboard
    case "trust-policy-leaderboard":
      return xrpc("ai.gftd.trust.leaderboard", entry.payload);
    // magatama:trust/trust-policy@1.0.0#score
    case "trust-policy-score":
      return xrpc("ai.gftd.trust.score", entry.payload);

    // ── tools-ozone:verification/verification@1.0.0 ──
    // tools-ozone:verification/verification@1.0.0#ozone-grant-verifications
    case "verification-ozone-grant-verifications":
      return xrpc("ai.gftd.apps.verification.ozoneGrantVerifications", entry.payload);
    // tools-ozone:verification/verification@1.0.0#ozone-list-verifications
    case "verification-ozone-list-verifications":
      return xrpc("ai.gftd.apps.verification.ozoneListVerifications", entry.payload);
    // tools-ozone:verification/verification@1.0.0#ozone-revoke-verifications
    case "verification-ozone-revoke-verifications":
      return xrpc("ai.gftd.apps.verification.ozoneRevokeVerifications", entry.payload);

    // ── app-bsky:video/video@1.0.0 ──
    // app-bsky:video/video@1.0.0#upload-video
    case "video-upload-video":
      return xrpc("ai.gftd.apps.video.uploadVideo", entry.payload);

    // ── magatama:web3/wallet@1.0.0 ──
    // magatama:web3/wallet@1.0.0#estimate-gas
    case "wallet-estimate-gas":
      return xrpc("ai.gftd.web3.estimateGas", entry.payload);
    // magatama:web3/wallet@1.0.0#send-eth
    case "wallet-send-eth":
      return xrpc("ai.gftd.web3.sendEth", entry.payload);
    // magatama:web3/wallet@1.0.0#send-transaction
    case "wallet-send-transaction":
      return xrpc("ai.gftd.web3.sendTransaction", entry.payload);
    // magatama:web3/wallet@1.0.0#sign-message
    case "wallet-sign-message":
      return xrpc("ai.gftd.web3.signMessage", entry.payload);
    // magatama:web3/wallet@1.0.0#sign-typed-data
    case "wallet-sign-typed-data":
      return xrpc("ai.gftd.web3.signTypedData", entry.payload);
    // magatama:web3/wallet@1.0.0#transfer-gcc
    case "wallet-transfer-gcc":
      return xrpc("ai.gftd.web3.transferGcc", entry.payload);
    // magatama:web3/wallet@1.0.0#transfer-token
    case "wallet-transfer-token":
      return xrpc("ai.gftd.web3.transferToken", entry.payload);
    // magatama:web3/wallet@1.0.0#verify-message
    case "wallet-verify-message":
      return xrpc("ai.gftd.web3.verifyMessage", entry.payload);

    // ── ai-gftd:wrpc-stream/wrpc-stream@1.0.0 ──
    // ai-gftd:wrpc-stream/wrpc-stream@1.0.0#close
    case "wrpc-stream-close":
      return xrpc("ai.gftd.apps.wrpc-stream.close", entry.payload);
    // ai-gftd:wrpc-stream/wrpc-stream@1.0.0#has-next
    case "wrpc-stream-has-next":
      return xrpc("ai.gftd.apps.wrpc-stream.hasNext", entry.payload);
    // ai-gftd:wrpc-stream/wrpc-stream@1.0.0#read
    case "wrpc-stream-read":
      return xrpc("ai.gftd.apps.wrpc-stream.read", entry.payload);

    // ── ai-gftd:yata/yata@1.0.0 ──
    // ai-gftd:yata/yata@1.0.0#graph-exec
    case "yata-graph-exec":
      return xrpc("ai.gftd.apps.yata.graphExec", entry.payload);

    default:
      console.warn(`[wrpc-binding] unknown write buffer entry type: ${entry.type}`);
  }
}
