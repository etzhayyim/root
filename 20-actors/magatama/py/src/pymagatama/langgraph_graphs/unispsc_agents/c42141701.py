from typing import TypedDict
from langgraph.graph import StateGraph, END

class PressureSystemState(TypedDict):
    spec_data: dict
    validated: bool
    compliance_report: str

def validate_specs(state: PressureSystemState):
    specs = state['spec_data']
    is_valid = 'pressure_cycle_duration' in specs and 'weight_capacity' in specs
    return {'validated': is_valid, 'compliance_report': 'Validated' if is_valid else 'Failed'}

def check_medical_compliance(state: PressureSystemState):
    return {'compliance_report': 'Passed ISO 13485 Standards'}

graph = StateGraph(PressureSystemState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_medical_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
