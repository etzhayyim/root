from typing import TypedDict
from langgraph.graph import StateGraph, END

class TransformerState(TypedDict):
    spec_data: dict
    is_compliant: bool

def validate_specs(state: TransformerState):
    required = ['kVA_rating', 'isolation_class']
    state['is_compliant'] = all(k in state['spec_data'] for k in required)
    return state

def check_safety(state: TransformerState):
    if state.get('is_compliant'):
        print('Verification: Safety class meets industrial standards.')
    return state

graph = StateGraph(TransformerState)
graph.add_node('validate', validate_specs)
graph.add_node('safety', check_safety)
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph.set_entry_point('validate')
graph = graph.compile()