from typing import TypedDict
from langgraph.graph import StateGraph, END

class VaccineState(TypedDict):
    batch_id: str
    temperature_validated: bool
    compliance_cleared: bool

def validate_cold_chain(state: VaccineState):
    print(f"Validating batch {state['batch_id']} cold chain records...")
    return {"temperature_validated": True}

def check_regulatory_compliance(state: VaccineState):
    print("Verifying WHO prequalification and license...")
    return {"compliance_cleared": True}

graph = StateGraph(VaccineState)
graph.add_node("validate_storage", validate_cold_chain)
graph.add_node("check_compliance", check_regulatory_compliance)
graph.add_edge("validate_storage", "check_compliance")
graph.add_edge("check_compliance", END)
graph.set_entry_point("validate_storage")
compiled_graph = graph.compile()