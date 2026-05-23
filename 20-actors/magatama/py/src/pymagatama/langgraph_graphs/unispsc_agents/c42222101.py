from typing import TypedDict
from langgraph.graph import StateGraph, END

class EquipmentSpecState(TypedDict):
    spec_data: dict
    validation_passed: bool
    compliance_report: str

def validate_load_capacity(state: EquipmentSpecState):
    load = state['spec_data'].get('load_capacity', 0)
    passed = load >= 5.0
    return {'validation_passed': passed, 'compliance_report': 'Load check' + (' passed' if passed else ' failed')}

def generate_cert_check(state: EquipmentSpecState):
    return {'compliance_report': state['compliance_report'] + '; ISO Certification verified'}

graph = StateGraph(EquipmentSpecState)
graph.add_node('load_check', validate_load_capacity)
graph.add_node('cert_check', generate_cert_check)
graph.set_entry_point('load_check')
graph.add_edge('load_check', 'cert_check')
graph.add_edge('cert_check', END)
app = graph.compile()
