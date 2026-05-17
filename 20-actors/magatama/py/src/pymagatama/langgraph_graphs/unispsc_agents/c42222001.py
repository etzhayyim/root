from typing import TypedDict
from langgraph.graph import StateGraph, END

class PumpState(TypedDict):
    spec_data: dict
    is_compliant: bool

def validate_medical_specs(state: PumpState):
    required = ['flow_rate_accuracy', 'iso_13485_certification']
    state['is_compliant'] = all(k in state['spec_data'] for k in required)
    return state

def check_regulatory_status(state: PumpState):
    state['is_compliant'] = state['is_compliant'] and state['spec_data'].get('regulatory_approval', False)
    return state

graph = StateGraph(PumpState)
graph.add_node('validate', validate_medical_specs)
graph.add_node('regulatory', check_regulatory_status)
graph.set_entry_point('validate')
graph.add_edge('validate', 'regulatory')
graph.add_edge('regulatory', END)
graph = graph.compile()