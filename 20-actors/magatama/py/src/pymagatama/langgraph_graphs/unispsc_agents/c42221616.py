from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcureState(TypedDict):
    spec_data: dict
    is_compliant: bool

def validate_medical_spec(state: ProcureState):
    required = ['sterilization', 'pressure_rating', 'iso_cert']
    state['is_compliant'] = all(k in state['spec_data'] for k in required)
    return state

def check_compliance(state: ProcureState):
    return 'compliant' if state['is_compliant'] else 'non_compliant'

graph = StateGraph(ProcureState)
graph.add_node('validate', validate_medical_spec)
graph.set_entry_point('validate')
graph.add_edge('validate', END)