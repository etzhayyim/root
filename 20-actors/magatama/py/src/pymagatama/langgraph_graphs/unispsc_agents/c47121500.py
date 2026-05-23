from typing import TypedDict
from langgraph.graph import StateGraph, END

class JanitorCartState(TypedDict):
    serial_number: str
    spec_compliance: bool
    inspection_result: str

def validate_specs(state: JanitorCartState):
    state['spec_compliance'] = len(state['serial_number']) > 0
    return state

def check_integrity(state: JanitorCartState):
    state['inspection_result'] = 'PASS' if state['spec_compliance'] else 'FAIL'
    return state

graph = StateGraph(JanitorCartState)
graph.add_node('validate', validate_specs)
graph.add_node('integrity_check', check_integrity)
graph.add_edge('validate', 'integrity_check')
graph.add_edge('integrity_check', END)
graph.set_entry_point('validate')
graph = graph.compile()
