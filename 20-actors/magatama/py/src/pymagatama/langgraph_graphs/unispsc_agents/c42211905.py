from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    item_id: str
    safety_verified: bool
    compliance_docs: list

def validate_ergonomics(state: ProcurementState):
    print(f"Validating ergonomic specs for {state['item_id']}")
    return {"safety_verified": True}

def check_materials(state: ProcurementState):
    print("Checking BPA-free and heat resistance compliance")
    return {"compliance_docs": ["BPA_Cert", "Heat_Res_Test"]}

graph = StateGraph(ProcurementState)
graph.add_node("validate_ergonomics", validate_ergonomics)
graph.add_node("check_materials", check_materials)
graph.set_entry_point("validate_ergonomics")
graph.add_edge("validate_ergonomics", "check_materials")
graph.add_edge("check_materials", END)
graph = graph.compile()
