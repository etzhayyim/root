from typing import TypedDict
from langgraph.graph import StateGraph, END

class LampState(TypedDict):
    specs: dict
    approved: bool
    error: str

def validate_specs(state: LampState):
    required = ['Wavelength', 'Power', 'Voltage']
    if all(k in state['specs'] for k in required):
        return {'approved': True}
    return {'approved': False, 'error': 'Missing required technical parameters'}

def route_by_validation(state: LampState):
    return 'process' if state['approved'] else END

graph = StateGraph(LampState)
graph.add_node('validate', validate_specs)
graph.add_node('process', lambda x: x)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_validation)
graph.add_edge('process', END)
graph = graph.compile()
