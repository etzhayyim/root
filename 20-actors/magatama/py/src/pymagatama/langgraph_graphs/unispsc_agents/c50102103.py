from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class NectarineState(TypedDict):
    inspection_data: dict
    approved: bool
    qc_passed: bool

def validate_quality(state: NectarineState) -> NectarineState:
    brix = state['inspection_data'].get('brix', 0)
    state['qc_passed'] = brix >= 12.0
    return state

def check_compliance(state: NectarineState) -> NectarineState:
    state['approved'] = state['qc_passed'] and 'pesticide_cert' in state['inspection_data']
    return state

graph = StateGraph(NectarineState)
graph.add_node('qc_check', validate_quality)
graph.add_node('compliance_check', check_compliance)
graph.set_entry_point('qc_check')
graph.add_edge('qc_check', 'compliance_check')
graph.add_edge('compliance_check', END)
graph = graph.compile()