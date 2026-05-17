from typing import TypedDict
from langgraph.graph import StateGraph, END

class LabEquipmentState(TypedDict):
    specs: dict
    validation_status: bool
    compliance_report: str

def validate_cooling_specs(state: LabEquipmentState):
    temp_range = state['specs'].get('temp_range', 0)
    validation = temp_range < 0
    return {'validation_status': validation, 'compliance_report': 'Validated against ISO standards' if validation else 'Requires review'}

def approval_step(state: LabEquipmentState):
    print('Proceeding with procurement approval...')
    return {'compliance_report': 'Approved'}

graph = StateGraph(LabEquipmentState)
graph.add_node('validate', validate_cooling_specs)
graph.add_node('approval', approval_step)
graph.add_edge('validate', 'approval')
graph.add_edge('approval', END)
graph.set_entry_point('validate')
graph = graph.compile()