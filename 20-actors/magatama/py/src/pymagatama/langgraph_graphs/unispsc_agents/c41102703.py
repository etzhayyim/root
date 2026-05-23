from typing import TypedDict
from langgraph.graph import StateGraph, END

class LightScatteringState(TypedDict):
    specs: dict
    validation_status: str

def validate_specs(state: LightScatteringState):
    if state['specs'].get('laser_wavelength_nm') > 0:
        return {'validation_status': 'PASSED'}
    return {'validation_status': 'FAILED'}

def route_verification(state: LightScatteringState):
    return 'VALIDATED' if state['validation_status'] == 'PASSED' else END

graph = StateGraph(LightScatteringState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
