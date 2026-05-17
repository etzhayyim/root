from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class LabEquipmentState(TypedDict):
    purity_level: float
    spec_compliance: bool
    validation_report: str

def validate_quartz_specs(state: LabEquipmentState):
    # Business logic for quartz pot validation
    is_pure = state['purity_level'] >= 99.99
    return {'spec_compliance': is_pure, 'validation_report': 'Validated' if is_pure else 'Failed'}

def finalize_procurement(state: LabEquipmentState):
    return {'validation_report': f'Procurement status: {state.get("spec_compliance")}'}

graph = StateGraph(LabEquipmentState)
graph.add_node("validate", validate_quartz_specs)
graph.add_node("finalize", finalize_procurement)
graph.set_entry_point("validate")
graph.add_edge("validate", "finalize")
graph.add_edge("finalize", END)
graph = graph.compile()