from ._pipeline import register, ExecuteRequest

def malak_agent_hook(req: ExecuteRequest) -> tuple[str, list[str]]:
    system = (
        "You are the malak cybercrime intelligence agent. "
        "You autonomously correlate TTPs, verify graph edges, and track threat actors. "
        "If you see a wallet address, suggest linking via linkWalletToActor BPMN. "
        "Keep responses highly analytical."
    )
    ctx = []
    if "apt28" in req.details.lower() or "fancy bear" in req.details.lower():
        ctx.append("idx.threatActor: matched known APT28 patterns. Consider extracting new TTPs.")
    if "wallet" in req.details.lower() or "btc" in req.details.lower():
        ctx.append("vertex.malak_wallet_address: pending correlation check. Recommend invoking linkWalletToActor.")
    
    ctx.append("mv.malak_dashboard_counts: active investigations count indicates high priority.")
    
    return system, ctx

def crypto_tracker_hook(req: ExecuteRequest) -> tuple[str, list[str]]:
    system = (
        "You are the Malak Crypto Flow Tracker. Your role is to analyze cryptocurrency "
        "transactions, identify mixing services (like Tornado Cash), trace funds across "
        "exchanges, and attribute financial flows to specific threat actors. "
        "Suggest blockchain tracing actions."
    )
    ctx = ["vertex.crypto_transaction: Cross-chain flow analysis active."]
    return system, ctx

def sns_tracker_hook(req: ExecuteRequest) -> tuple[str, list[str]]:
    system = (
        "You are the Malak SNS Correlation Tracker. Your role is to correlate social media accounts, "
        "handles, email addresses, and communication patterns to unmask the personas of threat actors. "
        "Suggest social graph mapping actions."
    )
    ctx = ["vertex.sns_account: Social graph correlation active."]
    return system, ctx

def honeypot_tracker_hook(req: ExecuteRequest) -> tuple[str, list[str]]:
    system = (
        "You are the Malak Honeypot Tracker. Your role is to actively register trap email addresses "
        "on suspicious and malicious sites. When inbound spam or phishing is received, extract the "
        "infrastructure IOCs (IPs, DNS, payloads) and attribute them to threat actors. "
        "Suggest payload isolation and blocking actions."
    )
    ctx = ["vertex.malak_honeypot_payload: Sinkhole parsing active."]
    return system, ctx

register("malak", malak_agent_hook)
register("public-malak", malak_agent_hook)
register("crypto-tracker", crypto_tracker_hook)
register("sns-tracker", sns_tracker_hook)
register("honeypot-tracker", honeypot_tracker_hook)
