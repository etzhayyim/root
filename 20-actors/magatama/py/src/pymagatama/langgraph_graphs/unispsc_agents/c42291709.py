from typing import TypedDict
from langgraph.graph import StateGraph, END

class SurgicalBladeState(TypedDict):
    blade_type: str
    material: str
    sterilization_status: bool
    compliance_ok: bool

def validate_material(state: SurgicalBladeState):
    # Business logic for stainless steel grade/coating verification
    return {"compliance_ok": state["material"] in ["surgical-grade-steel", "titanium"]}

def check_sterilization(state: SurgicalBladeState):
    # Logic to confirm ETO/Gamma sterilization records
    return {"sterilization_status": True}

graph = StateGraph(SurgicalBladeState)
graph.add_node("validate", validate_material)
graph.add_node("sterilization", check_sterilization)
graph.set_entry_point("validate")
graph.add_edge("validate", "sterilization")
graph.add_edge("sterilization", END)
compiled_graph = graph.compile()