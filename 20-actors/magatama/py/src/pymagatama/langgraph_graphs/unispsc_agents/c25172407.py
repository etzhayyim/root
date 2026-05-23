from typing import TypedDict
from langgraph.graph import StateGraph, END

class BreatherState(TypedDict):
    specs: dict
    validation_status: bool

def validate_specs(state: BreatherState):
    required = ['filtration_micron_rating', 'thread_type']
    state['validation_status'] = all(k in state['specs'] for k in required)
    return state

def check_compliance(state: BreatherState):
    if state['validation_status']:
        print('Compliance check passed.')
    else:
        print('Missing required technical specifications.')
    return state

graph = StateGraph(BreatherState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()
