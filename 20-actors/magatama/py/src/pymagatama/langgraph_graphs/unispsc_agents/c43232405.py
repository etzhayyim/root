from typing import TypedDict
from langgraph.graph import StateGraph, END

class DevSoftwareState(TypedDict):
    software_name: str
    security_check_passed: bool
    compliance_validated: bool

def validate_license(state: DevSoftwareState):
    print(f'Validating licensing for {state["software_name"]}')
    return {"compliance_validated": True}

def audit_security(state: DevSoftwareState):
    print(f'Running security scan for {state["software_name"]}')
    return {"security_check_passed": True}

graph = StateGraph(DevSoftwareState)
graph.add_node("validate", validate_license)
graph.add_node("security", audit_security)
graph.set_entry_point("validate")
graph.add_edge("validate", "security")
graph.add_edge("security", END)
app = graph.compile()