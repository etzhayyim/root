from typing import TypedDict
from langgraph.graph import StateGraph, END

class RestraintState(TypedDict):
    spec_data: dict
    compliance_passed: bool

def validate_spec(state: RestraintState):
    # Business logic for verifying medical compliance
    required = ['material_safety', 'tensile_test']
    all_present = all(k in state['spec_data'] for k in required)
    return {'compliance_passed': all_present}

def finalize_order(state: RestraintState):
    return {'compliance_passed': True}

graph = StateGraph(RestraintState)
graph.add_node('validate', validate_spec)
graph.add_node('finalize', finalize_order)
graph.add_edge('validate', 'finalize')
graph.set_entry_point('validate')
graph.add_edge('finalize', END)
graph = graph.compile()