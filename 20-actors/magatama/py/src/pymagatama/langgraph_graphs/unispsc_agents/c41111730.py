from typing import TypedDict
from langgraph.graph import StateGraph, END

class MicroscopeState(TypedDict):
    spec_data: dict
    validation_passed: bool
    error_log: list

def validate_optics(state: MicroscopeState):
    na = state['spec_data'].get('NA', 0)
    if na <= 0: return {'validation_passed': False, 'error_log': ['Invalid Numerical Aperture']}
    return {'validation_passed': True}

graph = StateGraph(MicroscopeState)
graph.add_node('validate', validate_optics)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()