from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class LabEquipmentState(TypedDict):
    equipment_id: str
    spec_requirements: dict
    validation_passed: bool
    compliance_report: str

def validate_specs(state: LabEquipmentState):
    # Logic to verify electrical and safety specs for electrophoresis
    state['validation_passed'] = all(k in state['spec_requirements'] for k in ['voltage', 'safety_cert'])
    return state

def generate_report(state: LabEquipmentState):
    state['compliance_report'] = 'Validated according to ISO laboratory standards.'
    return state

graph = StateGraph(LabEquipmentState)
graph.add_node('validate', validate_specs)
graph.add_node('report', generate_report)
graph.add_edge('validate', 'report')
graph.add_edge('report', END)
graph.set_entry_point('validate')
graph = graph.compile()
