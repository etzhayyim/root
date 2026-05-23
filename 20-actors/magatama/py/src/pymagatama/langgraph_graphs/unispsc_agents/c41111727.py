from langgraph.graph import StateGraph, END
from typing import TypedDict

class MicroscopeState(TypedDict):
    specs: dict
    validated: bool

def validate_specs(state: MicroscopeState):
    required = ['magnification', 'resolution']
    state['validated'] = all(k in state['specs'] for k in required)
    return state

def check_calibration(state: MicroscopeState):
    print('Verifying ISO calibration standards...')
    return state

graph = StateGraph(MicroscopeState)
graph.add_node('validate', validate_specs)
graph.add_node('calibrate', check_calibration)
graph.set_entry_point('validate')
graph.add_edge('validate', 'calibrate')
graph.add_edge('calibrate', END)
graph = graph.compile()
