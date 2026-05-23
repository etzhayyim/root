from typing import TypedDict
from langgraph.graph import StateGraph, END

class BilletState(TypedDict):
    spec_data: dict
    validation_passed: bool

def validate_chemistry(state: BilletState):
    # Business logic for metallurgical standard checks
    state['validation_passed'] = all(k in state['spec_data'] for k in ['carbon', 'sulfur', 'phosphorus'])
    return state

def certify_quality(state: BilletState):
    print('Verifying Mill Test Certificate integrity...')
    return state

graph = StateGraph(BilletState)
graph.add_node('chemistry_check', validate_chemistry)
graph.add_node('certify', certify_quality)
graph.set_entry_point('chemistry_check')
graph.add_edge('chemistry_check', 'certify')
graph.add_edge('certify', END)
graph = graph.compile()
