from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class PipeState(TypedDict):
    specs: dict
    validation_passed: bool
    compliance_report: str

def validate_pressure(state: PipeState):
    pressure = state['specs'].get('pressure_rating', 0)
    state['validation_passed'] = pressure > 0
    state['compliance_report'] = 'Pressure check passed' if state['validation_passed'] else 'Pressure failure'
    return state

def check_standards(state: PipeState):
    has_asme = 'ASME' in state['specs'].get('certifications', [])
    state['validation_passed'] = state['validation_passed'] and has_asme
    return state

graph = StateGraph(PipeState)
graph.add_node('validate_pressure', validate_pressure)
graph.add_node('check_standards', check_standards)
graph.set_entry_point('validate_pressure')
graph.add_edge('validate_pressure', 'check_standards')
graph.add_edge('check_standards', END)
graph = graph.compile()
