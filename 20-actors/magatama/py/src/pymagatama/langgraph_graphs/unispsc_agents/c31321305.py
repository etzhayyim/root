from typing import TypedDict
from langgraph.graph import StateGraph, END

class RivetAssemblyState(TypedDict):
    spec_data: dict
    validation_score: float
    is_approved: bool

def validate_structural_specs(state: RivetAssemblyState):
    specs = state['spec_data']
    valid = specs.get('yield_strength_mpa', 0) > 400 and 'standard' in specs.get('coating_spec', '')
    return {'validation_score': 1.0 if valid else 0.0, 'is_approved': valid}

graph = StateGraph(RivetAssemblyState)
graph.add_node('validate', validate_structural_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()