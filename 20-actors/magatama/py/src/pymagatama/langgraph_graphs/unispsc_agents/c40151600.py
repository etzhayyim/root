from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class CompressorState(TypedDict):
    specs: dict
    validation_passed: bool
    compliance_report: str

def validate_pressure_specs(state: CompressorState):
    pressure = state['specs'].get('pressure', 0)
    state['validation_passed'] = pressure > 0 and pressure < 100
    return state

def check_compliance(state: CompressorState):
    if state['validation_passed']:
        state['compliance_report'] = 'Standard compliant'
    else:
        state['compliance_report'] = 'Safety risk: Pressure rating non-compliant'
    return state

graph = StateGraph(CompressorState)
graph.add_node('validate', validate_pressure_specs)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()
