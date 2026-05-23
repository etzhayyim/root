from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CTScannerState(TypedDict):
    equipment_id: str
    regulatory_compliant: bool
    site_verified: bool

def validate_certification(state: CTScannerState):
    # Simulate regulatory check
    return {"regulatory_compliant": True}

def verify_site(state: CTScannerState):
    # Simulate room shielding verification
    return {"site_verified": True}

def deploy_unit(state: CTScannerState):
    print(f"Deploying unit {state['equipment_id']}")
    return {"site_verified": True}

graph = StateGraph(CTScannerState)
graph.add_node("certify", validate_certification)
graph.add_node("site_check", verify_site)
graph.add_node("deploy", deploy_unit)
graph.set_entry_point("certify")
graph.add_edge("certify", "site_check")
graph.add_edge("site_check", "deploy")
graph.add_edge("deploy", END)
graph = graph.compile()
