from typing import TypedDict
from langgraph.graph import StateGraph, END

class OvertubeState(TypedDict):
    spec_data: dict
    validation_results: list
    is_approved: bool

def validate_specs(state: OvertubeState):
    required = ['Sterilization Method', 'Regulatory Approval']
    valid = all(k in state['spec_data'] for k in required)
    return {'validation_results': ['Specs validated: ' + str(valid)], 'is_approved': valid}

def route_by_approval(state: OvertubeState):
    return 'approved' if state['is_approved'] else END

graph = StateGraph(OvertubeState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()
