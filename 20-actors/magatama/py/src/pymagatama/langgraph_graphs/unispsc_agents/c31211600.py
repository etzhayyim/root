from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class AdditiveState(TypedDict):
    additive_type: str
    spec_data: dict
    approved: bool

def validate_safety_data(state: AdditiveState):
    # Logic to verify SDS and VOC compliance
    return {"approved": state['spec_data'].get('voc_compliant', False)}

def evaluate_viscosity(state: AdditiveState):
    # Logic to evaluate viscosity specs
    return {"approved": state['spec_data'].get('viscosity_range', 0) > 0}

graph = StateGraph(AdditiveState)
graph.add_node("safety_check", validate_safety_data)
graph.add_node("viscosity_check", evaluate_viscosity)
graph.add_edge("safety_check", "viscosity_check")
graph.add_edge("viscosity_check", END)
graph.set_entry_point("safety_check")
compiled_graph = graph.compile()
