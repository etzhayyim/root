from typing import TypedDict
from langgraph.graph import StateGraph, END

class PolisherState(TypedDict):
    spec_data: dict
    is_compliant: bool

def validate_specs(state: PolisherState):
    required = ['calibration_certification', 'surface_roughness_tolerance']
    state['is_compliant'] = all(k in state['spec_data'] for k in required)
    return state

def check_regulatory(state: PolisherState):
    print('Checking Ophthalmic regulation compliance...')
    return state

graph = StateGraph(PolisherState)
graph.add_node('validate', validate_specs)
graph.add_node('regulatory', check_regulatory)
graph.set_entry_point('validate')
graph.add_edge('validate', 'regulatory')
graph.add_edge('regulatory', END)
graph = graph.compile()
