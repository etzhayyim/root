from typing import TypedDict
from langgraph.graph import StateGraph, END

class OfficeSupplyState(TypedDict):
    item_name: str
    material_certified: bool
    quantity: int
    qc_passed: bool

def validate_materials(state: OfficeSupplyState) -> OfficeSupplyState:
    state['material_certified'] = True
    return state

def run_qc(state: OfficeSupplyState) -> OfficeSupplyState:
    state['qc_passed'] = state['quantity'] > 0
    return state

graph = StateGraph(OfficeSupplyState)
graph.add_node("validate_materials", validate_materials)
graph.add_node("run_qc", run_qc)
graph.set_entry_point("validate_materials")
graph.add_edge("validate_materials", "run_qc")
graph.add_edge("run_qc", END)
graph = graph.compile()