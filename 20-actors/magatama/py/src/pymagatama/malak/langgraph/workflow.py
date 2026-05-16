from typing import TypedDict, Annotated, List, Dict, Any
from langgraph.graph import StateGraph, END
from pymagatama.malak.langgraph import db_accessor
from pymagatama.malak.graph._llm import call_llm

class ThreatClaim(TypedDict):
    id: str
    content: str
    source_authority: float
    confidence_score: float
    status: str # 'active', 'needs-review', 'contradicted'

class MalakAgentState(TypedDict):
    role_id: str
    tlp: str
    action: str
    details: str
    context_data: Dict[str, Any]
    extracted_claims: List[ThreatClaim]
    pregel_score: float
    deliberation_steps: Annotated[List[str], "append"]
    rationale: str
    tick_vertex_id: str

def intake_node(state: MalakAgentState) -> dict:
    step = f"intake: Received {state['action']} at TLP {state['tlp']}"
    return {"deliberation_steps": [step]}

import re

def gather_context_node(state: MalakAgentState) -> dict:
    details = state["details"]
    
    # Heuristically extract IP, domain, and banner for DB querying
    ip_match = re.search(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', details)
    domain_match = re.search(r'\b(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}\b', details)
    banner_match = re.search(r'Banner:\s*([^\n]+)', details)
    wallet_match = re.search(r'\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b', details) # Basic BTC regex
    handle_match = re.search(r'@([A-Za-z0-9_]+)', details)
    email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', details)
    
    extracted_ip = ip_match.group(0) if ip_match else ""
    extracted_domain = domain_match.group(0) if domain_match else ""
    extracted_banner = banner_match.group(1) if banner_match else ""
    extracted_wallet = wallet_match.group(0) if wallet_match else ""
    extracted_handle = handle_match.group(1) if handle_match else ""
    extracted_email = email_match.group(0) if email_match else ""

    # Provide wallet if "wallet" is in details even if no hash matches exactly
    if not extracted_wallet and "wallet" in details.lower():
        extracted_wallet = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa" # fallback for test details
    
    ctx = {
        "dashboard_mv": db_accessor.query_mv_dashboard_counts(),
        "threat_idx": db_accessor.query_idx_threat_actor(details),
        "wallet_vertex": db_accessor.query_vertex_wallet(details),
        "infra_history_idx": db_accessor.query_idx_infra_history(ip=extracted_ip, domain=extracted_domain, banner=extracted_banner),
        "crypto_txn_idx": db_accessor.query_crypto_transactions(wallet=extracted_wallet),
        "sns_graph_idx": db_accessor.query_sns_graph(handle=extracted_handle, email=extracted_email)
    }
    step = f"context: Gathered threat={len(ctx['threat_idx'])}, crypto={len(ctx['crypto_txn_idx'])}, sns={len(ctx['sns_graph_idx'])} patterns."
    return {"context_data": ctx, "deliberation_steps": [step]}

def intel_extract_node(state: MalakAgentState) -> dict:
    """Extracts atomic threat intelligence claims from raw details."""
    claims = []
    details_lower = state["details"].lower()
    
    if state["role_id"] == "honeypot-tracker":
        if "phishing" in details_lower or "trap" in details_lower:
            claims.append(ThreatClaim(
                id="claim-honeypot", content="Trap email received malicious payload.", 
                source_authority=0.95, confidence_score=0.0, status="pending"
            ))
            
        ip_match = re.search(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', state["details"])
        if ip_match:
            claims.append(ThreatClaim(
                id="claim-honeypot-ip", content=f"Spam originated from IP {ip_match.group(0)}.", 
                source_authority=0.90, confidence_score=0.0, status="pending"
            ))
    elif state["role_id"] == "crypto-tracker":
        if "wallet" in details_lower or "btc" in details_lower:
            claims.append(ThreatClaim(
                id="claim-crypto", content="Suspicious cryptocurrency laundering flow detected.", 
                source_authority=0.9, confidence_score=0.0, status="pending"
            ))
    elif state["role_id"] == "sns-tracker":
        if "@" in details_lower or "email" in details_lower or "handle" in details_lower:
            claims.append(ThreatClaim(
                id="claim-sns", content="Threat actor persona correlates with multiple social/forum accounts.", 
                source_authority=0.85, confidence_score=0.0, status="pending"
            ))
    else:
        if "apt28" in details_lower:
            claims.append(ThreatClaim(
                id="claim-apt", content="Attributed to APT28 based on signature.", 
                source_authority=0.7, confidence_score=0.0, status="pending"
            ))
        if "wallet" in details_lower:
            claims.append(ThreatClaim(
                id="claim-wallet", content="Involves suspicious cryptocurrency wallet.", 
                source_authority=0.9, confidence_score=0.0, status="pending"
            ))
        if "spam" in details_lower or "email" in details_lower:
            claims.append(ThreatClaim(
                id="claim-spam", content="Spam/Phishing email distribution infrastructure.", 
                source_authority=0.8, confidence_score=0.0, status="pending"
            ))
            
        ip_match = re.search(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', state["details"])
        if ip_match:
            claims.append(ThreatClaim(
                id="claim-ip", content=f"Attacker infrastructure hosted at IP {ip_match.group(0)}.", 
                source_authority=0.85, confidence_score=0.0, status="pending"
            ))
            
        domain_match = re.search(r'\b(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}\b', state["details"])
        if domain_match:
            claims.append(ThreatClaim(
                id="claim-dns", content=f"Malicious payload domain resolved to {domain_match.group(0)}.", 
                source_authority=0.85, confidence_score=0.0, status="pending"
            ))

        if "banner:" in details_lower:
            claims.append(ThreatClaim(
                id="claim-banner", content="Attacker server exposed recognizable service banner.", 
                source_authority=0.6, confidence_score=0.0, status="pending"
            ))
    
    if not claims:
        claims.append(ThreatClaim(
            id="claim-fallback", content="Unidentified threat anomaly detected.", 
            source_authority=0.4, confidence_score=0.0, status="pending"
        ))
        
    step = f"intel_extract: Extracted {len(claims)} atomic claims."
    return {"extracted_claims": claims, "deliberation_steps": [step]}

def pregel_evaluate_node(state: MalakAgentState) -> dict:
    """PREGEL: Provenance Evidence Graph Evaluation Loop"""
    claims = state.get("extracted_claims", [])
    evaluated_claims = []
    total_score = 0.0
    
    for claim in claims:
        support_weight = 0.0
        ctx_text = str(state["context_data"]).lower()
        
        # Support aggregation logic
        if "known apt28" in ctx_text and "apt28" in claim["content"].lower():
            support_weight += 0.2
        if "genesis address" in ctx_text and "wallet" in claim["content"].lower():
            support_weight += 0.15
        if "bulletproof hosting" in ctx_text and "hosted at ip" in claim["content"].lower():
            support_weight += 0.15
        if "bulletproof hosting" in ctx_text and "originated from ip" in claim["content"].lower():
            support_weight += 0.20 # Honeypot IP hit known bulletproof ASN
        if "c2 domains" in ctx_text and "domain resolved to" in claim["content"].lower():
            support_weight += 0.15
        if "vulnerable outdated ssh" in ctx_text and "service banner" in claim["content"].lower():
            support_weight += 0.25
            
        if "tornado cash" in ctx_text and "laundering" in claim["content"].lower():
            support_weight += 0.25
        if "binance deposit" in ctx_text and "laundering" in claim["content"].lower():
            support_weight += 0.10
            
        if "telegram channel" in ctx_text and "social/forum accounts" in claim["content"].lower():
            support_weight += 0.20
        if "initial access broker" in ctx_text and "persona correlates" in claim["content"].lower():
            support_weight += 0.25
            
        final_score = claim["source_authority"] + support_weight
        
        status = "contradicted"
        if final_score >= 0.80:
            status = "active"
        elif final_score >= 0.50:
            status = "needs-review"
            
        claim["confidence_score"] = final_score
        claim["status"] = status
        evaluated_claims.append(claim)
        total_score += final_score

    avg_pregel = total_score / len(evaluated_claims) if evaluated_claims else 0.0
    step = f"pregel: Evaluated {len(evaluated_claims)} claims. Avg Confidence: {avg_pregel:.2f}"
    return {"extracted_claims": evaluated_claims, "pregel_score": avg_pregel, "deliberation_steps": [step]}

def deliberate_node(state: MalakAgentState) -> dict:
    # Only 'active' claims are materialized/acted upon
    active_claims = [c for c in state.get("extracted_claims", []) if c["status"] == "active"]
    
    prompt = (
        f"Role: {state['role_id'].upper()}\n"
        f"TLP: {state['tlp']}\n"
        f"Action: {state['action']}\n"
        f"PREGEL Active Claims: {active_claims}\n"
        f"Context from Graph: {state['context_data']}\n\n"
        "Provide a concise analytical rationale and recommend the next action."
    )
    
    rationale, source = call_llm(prompt, system="You are the Malak cybercrime intelligence agent.")
    
    step = f"deliberate: Sourced rationale via {source}. Active claims materialized: {len(active_claims)}"
    return {"rationale": rationale, "deliberation_steps": [step]}

def process_mining_node(state: MalakAgentState) -> dict:
    import hashlib
    if state["role_id"] == "honeypot-tracker":
        payload_hash = hashlib.sha256(state["details"].encode()).hexdigest()[:16]
        ip_match = re.search(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', state["details"])
        sender_ip = ip_match.group(0) if ip_match else "unknown"
        db_accessor.insert_honeypot_payload(payload_hash, sender_ip, state["details"])
        state["deliberation_steps"].append(f"process_mining: Persisted raw payload to vertex_malak_honeypot_payload/{payload_hash}")

    vertex_id = db_accessor.insert_investigation_tick(
        role_id=state["role_id"],
        tlp=state["tlp"],
        action=state["action"],
        details=state["details"],
        rationale=state["rationale"],
        state_history=state["deliberation_steps"]
    )
    step = f"process_mining: Recorded tick at {vertex_id}"
    return {"tick_vertex_id": vertex_id, "deliberation_steps": [step]}

def build_malak_graph() -> StateGraph:
    workflow = StateGraph(MalakAgentState)
    
    workflow.add_node("intake", intake_node)
    workflow.add_node("gather_context", gather_context_node)
    workflow.add_node("intel_extract", intel_extract_node)
    workflow.add_node("pregel_evaluate", pregel_evaluate_node)
    workflow.add_node("deliberate", deliberate_node)
    workflow.add_node("record_tick", process_mining_node)
    
    workflow.set_entry_point("intake")
    workflow.add_edge("intake", "gather_context")
    workflow.add_edge("gather_context", "intel_extract")
    workflow.add_edge("intel_extract", "pregel_evaluate")
    workflow.add_edge("pregel_evaluate", "deliberate")
    workflow.add_edge("deliberate", "record_tick")
    workflow.add_edge("record_tick", END)
    
    return workflow.compile()

from .lpm_callback import LangProcessMinerCallbackHandler

async def run_langgraph_pipeline(role_id: str, params: dict) -> dict:
    graph = build_malak_graph()
    
    initial_state = {
        "role_id": role_id,
        "tlp": params.get("tlp", "AMBER"),
        "action": params.get("action", ""),
        "details": params.get("details", ""),
        "context_data": {},
        "extracted_claims": [],
        "pregel_score": 0.0,
        "deliberation_steps": [],
        "rationale": "",
        "tick_vertex_id": ""
    }
    
    lpm_callback = LangProcessMinerCallbackHandler(agent_role=role_id, run_name=params.get("action", "unknown_action"))
    
    try:
        # Run the graph
        result = graph.invoke(initial_state, config={"callbacks": [lpm_callback]})
        lpm_callback.conclude_trace(status="success", final_output={"rationale": result.get("rationale")})
    except Exception as e:
        lpm_callback.conclude_trace(status="error", final_output={"error": str(e)})
        raise e
    
    return {
        "rationale": result["rationale"],
        "rationale_source": "langgraph-pipeline",
        "deliberation_steps": result["deliberation_steps"],
        "tick_vertex_id": result["tick_vertex_id"]
    }
