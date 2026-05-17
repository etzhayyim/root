from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ParaffinState(TypedDict):
    specs: dict
    validation_passed: bool
    safety_check: str

def validate_specs(state: ParaffinState):
    temp_range = state['specs'].get('temp_range', 0)
    state['validation_passed'] = 50 <= temp_range <= 60
    return state

def check_compliance(state: ParaffinState):
    state['safety_check'] = 'IEC_60601_VERIFIED' if state['validation_passed'] else 'FAIL'
    return state

graph = StateGraph(ParaffinState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()