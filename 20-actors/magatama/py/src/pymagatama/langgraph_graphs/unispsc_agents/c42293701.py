from typing import TypedDict
from langgraph.graph import StateGraph, END

class SurgicalDeviceState(TypedDict):
    device_id: str
    compliance_cleared: bool
    sterilization_verified: bool

def validate_compliance(state: SurgicalDeviceState):
    print(f'Validating medical compliance for {state["device_id"]}')
    return {"compliance_cleared": True}

def verify_sterility(state: SurgicalDeviceState):
    print('Verifying sterile packaging and material integrity.')
    return {"sterilization_verified": True}

graph = StateGraph(SurgicalDeviceState)
graph.add_node("validate", validate_compliance)
graph.add_node("sterilize", verify_sterility)
graph.add_edge("validate", "sterilize")
graph.add_edge("sterilize", END)
graph.set_entry_point("validate")
compiled_graph = graph.compile()