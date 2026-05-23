from typing import TypedDict
from langgraph.graph import StateGraph, END

class CapSpecState(TypedDict):
    spec_data: dict
    is_compliant: bool

def validate_cap_specs(state: CapSpecState):
    required = ['material_composition', 'seal_integrity_rating']
    compliance = all(k in state['spec_data'] for k in required)
    return {'is_compliant': compliance}

workflow = StateGraph(CapSpecState)
workflow.add_node('validator', validate_cap_specs)
workflow.set_entry_point('validator')
workflow.add_edge('validator', END)
graph = workflow.compile()
