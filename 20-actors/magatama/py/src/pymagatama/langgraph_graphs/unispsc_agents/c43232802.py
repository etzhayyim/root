from typing import TypedDict
from langgraph.graph import StateGraph, END

class NetOSState(TypedDict):
    software_version: str
    compatibility_check: bool
    security_validation: bool

def check_compatibility(state: NetOSState):
    print(f"Validating compatibility for {state['software_version']}")
    return {"compatibility_check": True}

def validate_security(state: NetOSState):
    print("Running security vulnerability scan on package...")
    return {"security_validation": True}

graph = StateGraph(NetOSState)
graph.add_node("check_comp", check_compatibility)
graph.add_node("sec_val", validate_security)
graph.set_entry_point("check_comp")
graph.add_edge("check_comp", "sec_val")
graph.add_edge("sec_val", END)
app = graph.compile()