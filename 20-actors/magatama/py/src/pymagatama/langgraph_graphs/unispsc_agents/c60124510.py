from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class WaterwayState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    approved: bool

def validate_spec(state: WaterwayState):
    errors = []
    if 'leak_test' not in state['spec_data']: errors.append('Missing leak test results')
    return {'validation_errors': errors}

def approve_procurement(state: WaterwayState):
    return {'approved': len(state['validation_errors']) == 0}

graph = StateGraph(WaterwayState)
graph.add_node('validate', validate_spec)
graph.add_node('approve', approve_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
app = graph.compile()
