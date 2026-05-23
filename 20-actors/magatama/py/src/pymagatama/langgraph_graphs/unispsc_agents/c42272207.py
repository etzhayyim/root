from langgraph.graph import StateGraph, END
from typing import TypedDict

class VentState(TypedDict):
    spec_data: dict
    validation_passed: bool

def validate_clinical_standards(state: VentState):
    state['validation_passed'] = 'ISO13485' in state['spec_data'].get('certs', [])
    return state

def check_pressure_limits(state: VentState):
    val = state['spec_data'].get('working_pressure', 0)
    state['validation_passed'] = state['validation_passed'] and (0 < val < 200)
    return state

graph = StateGraph(VentState)
graph.add_node('validate_cert', validate_clinical_standards)
graph.add_node('check_pressure', check_pressure_limits)
graph.set_entry_point('validate_cert')
graph.add_edge('validate_cert', 'check_pressure')
graph.add_edge('check_pressure', END)
graph = graph.compile()
