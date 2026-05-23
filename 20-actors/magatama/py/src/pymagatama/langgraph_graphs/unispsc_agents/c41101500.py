from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class LabEquipmentState(TypedDict):
    equipment_id: str
    specifications: dict
    validation_status: bool
    compliance_report: List[str]

def validate_specs(state: LabEquipmentState):
    specs = state['specifications']
    is_valid = specs.get('rpm', 0) > 0 and 'material' in specs
    return {'validation_status': is_valid}

def generate_compliance(state: LabEquipmentState):
    if state['validation_status']:
        return {'compliance_report': ['ISO-9001', 'CE-Mark']}
    return {'compliance_report': ['NON-COMPLIANT']}

graph = StateGraph(LabEquipmentState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', generate_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
