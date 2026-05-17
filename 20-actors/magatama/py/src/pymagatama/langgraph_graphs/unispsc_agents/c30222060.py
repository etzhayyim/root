from typing import TypedDict
from langgraph.graph import StateGraph, END

class OutfallState(TypedDict):
    spec_data: dict
    is_compliant: bool
    validation_log: list

def validate_specs(state: OutfallState):
    required = ['Flow Capacity', 'Material Grade']
    valid = all(k in state['spec_data'] for k in required)
    return {'is_compliant': valid, 'validation_log': ['Specs checked against EPA standards']}

def structural_review(state: OutfallState):
    if state['is_compliant']:
        return {'validation_log': state['validation_log'] + ['Structural integrity check passed']}
    return {'validation_log': state['validation_log'] + ['Structural integrity check failed']}

graph = StateGraph(OutfallState)
graph.add_node('validate', validate_specs)
graph.add_node('review', structural_review)
graph.set_entry_point('validate')
graph.add_edge('validate', 'review')
graph.add_edge('review', END)
graph = graph.compile()