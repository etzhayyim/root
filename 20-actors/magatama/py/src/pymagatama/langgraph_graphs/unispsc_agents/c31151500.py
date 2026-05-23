from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class RopeProcurementState(TypedDict):
    rope_type: str
    material: str
    tensile_strength: float
    verified: bool

def validate_rope_specs(state: RopeProcurementState):
    # Basic validation logic for industrial rope grade
    min_strength = 5.0
    is_valid = state['tensile_strength'] >= min_strength
    return {'verified': is_valid}

workflow = StateGraph(RopeProcurementState)
workflow.add_node('validate', validate_rope_specs)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()
