from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class BeamState(TypedDict):
    specs: dict
    validation_passed: bool
    errors: List[str]

def validate_specs(state: BeamState):
    required = ['alloy', 'tensile_strength']
    errors = [f'Missing {f}' for f in required if f not in state['specs']]
    return {'validation_passed': len(errors) == 0, 'errors': errors}

def process_procurement(state: BeamState): return state

graph = StateGraph(BeamState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', process_procurement)
graph.add_edge('validate', 'approve')
graph.set_entry_point('validate')
graph.add_edge('approve', END)
graph = graph.compile()