from typing import TypedDict
from langgraph.graph import StateGraph, END

class BearingState(TypedDict):
    specs: dict
    validated: bool
    error: str

def validate_specs(state: BearingState):
    required = ['inner_d', 'outer_d', 'load_rating']
    if all(k in state['specs'] for k in required):
        return {'validated': True}
    return {'validated': False, 'error': 'Missing required technical specs'}

def check_compliance(state: BearingState):
    if state.get('validated') and 'iso_cert' in state['specs']:
        print('Compliance check passed')
    return {}

graph = StateGraph(BearingState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
