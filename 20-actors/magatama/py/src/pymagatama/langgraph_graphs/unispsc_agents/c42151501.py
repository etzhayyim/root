from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CuringLightState(TypedDict):
    model_id: str
    wavelength: int
    intensity: int
    is_compliant: bool

def validate_tech_specs(state: CuringLightState):
    # ISO 10650 check
    if state['wavelength'] < 400 or state['wavelength'] > 500:
         state['is_compliant'] = False
    else:
         state['is_compliant'] = True
    return state

def approve_procurement(state: CuringLightState):
    print(f"Device {state['model_id']} compliance: {state['is_compliant']}")
    return state

graph = StateGraph(CuringLightState)
graph.add_node("validate", validate_tech_specs)
graph.add_node("approve", approve_procurement)
graph.add_edge("validate", "approve")
graph.add_edge("approve", END)
graph.set_entry_point("validate")
graph = graph.compile()