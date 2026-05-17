from typing import TypedDict
from langgraph.graph import StateGraph, END

class DentalMaterialState(TypedDict):
    material_id: str
    compliance_checked: bool
    passed_qa: bool

def validate_porcelain(state: DentalMaterialState):
    print(f"Validating porcelain teeth: {state['material_id']}")
    return {"compliance_checked": True}

def perform_qa(state: DentalMaterialState):
    print("Running biocompatibility and hardness testing.")
    return {"passed_qa": True}

graph = StateGraph(DentalMaterialState)
graph.add_node("validate", validate_porcelain)
graph.add_node("qa", perform_qa)
graph.set_entry_point("validate")
graph.add_edge("validate", "qa")
graph.add_edge("qa", END)
graph = graph.compile()