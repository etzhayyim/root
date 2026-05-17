from typing import TypedDict
from langgraph.graph import StateGraph, END

class FermentationState(TypedDict):
    specs: dict
    validated: bool
    compliance_flag: bool

def validate_specs(state: FermentationState):
    # Perform check for bioreactor critical parameters
    required = ['material', 'sterilization_type']
    state['validated'] = all(k in state['specs'] for k in required)
    return state

def check_compliance(state: FermentationState):
    # Dual-use export control screening logic
    state['compliance_flag'] = state['specs'].get('volume', 0) < 500
    return state

graph = StateGraph(FermentationState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()