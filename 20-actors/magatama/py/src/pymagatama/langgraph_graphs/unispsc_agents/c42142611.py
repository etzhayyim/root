from langgraph.graph import StateGraph, END
from typing import TypedDict

class SyringeState(TypedDict):
    syringe_type: str
    is_sterile: bool
    compliance_checked: bool

def validate_medical_grade(state: SyringeState):
    state['compliance_checked'] = state['is_sterile'] and state['syringe_type'] == 'tuberculin'
    return state

def route_verification(state: SyringeState):
    return 'valid' if state['compliance_checked'] else 'failed'

graph = StateGraph(SyringeState)
graph.add_node('validate', validate_medical_grade)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()