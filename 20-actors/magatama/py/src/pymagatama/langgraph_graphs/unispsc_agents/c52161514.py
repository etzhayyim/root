from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class HeadphoneState(TypedDict):
    model: str
    specs: dict
    approved: bool

def validate_specs(state: HeadphoneState):
    required = ['impedance_ohms', 'connection_type']
    state['approved'] = all(k in state['specs'] for k in required)
    return state

def check_compliance(state: HeadphoneState):
    if state.get('approved'):
        print(f'Validating {state['model']}...')
    return 'end'

graph = StateGraph(HeadphoneState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()