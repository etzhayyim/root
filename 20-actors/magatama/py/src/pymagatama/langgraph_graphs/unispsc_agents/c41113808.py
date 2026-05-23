from typing import TypedDict
from langgraph.graph import StateGraph, END

class GravimeterState(TypedDict):
    spec_data: dict
    validation_passed: bool
    export_control_verified: bool

def validate_specs(state: GravimeterState):
    state['validation_passed'] = all(k in state['spec_data'] for k in ['precision', 'calibration'])
    return state

def check_export_compliance(state: GravimeterState):
    state['export_control_verified'] = True
    return state

graph = StateGraph(GravimeterState)
graph.add_node('validate', validate_specs)
graph.add_node('export_check', check_export_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export_check')
graph.add_edge('export_check', END)
graph = graph.compile()
