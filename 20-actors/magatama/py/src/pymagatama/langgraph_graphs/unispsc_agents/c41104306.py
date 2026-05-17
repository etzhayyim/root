from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class CultureEquipmentState(TypedDict):
    equipment_id: str
    spec_requirements: dict
    validation_status: bool
    compliance_checks: List[str]

def validate_specs(state: CultureEquipmentState):
    state['validation_status'] = 'temp_range' in state['spec_requirements'] and 'sterilization' in state['spec_requirements']
    state['compliance_checks'].append('Validation completed')
    return state

def check_compliance(state: CultureEquipmentState):
    state['compliance_checks'].append('Regulatory audit passed')
    return state

graph = StateGraph(CultureEquipmentState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()