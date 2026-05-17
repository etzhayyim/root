from typing import TypedDict
from langgraph.graph import StateGraph, END

class AesculusState(TypedDict):
    botanical_name: str
    certification: str
    inspection_passed: bool

def validate_botany(state: AesculusState):
    state['inspection_passed'] = state['botanical_name'].startswith('Aesculus')
    return state

def check_compliance(state: AesculusState):
    state['inspection_passed'] = state['inspection_passed'] and (state['certification'] is not None)
    return state

graph = StateGraph(AesculusState)
graph.add_node('validate', validate_botany)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()