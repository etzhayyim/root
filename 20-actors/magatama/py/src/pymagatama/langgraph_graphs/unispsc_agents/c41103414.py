from typing import TypedDict
from langgraph.graph import StateGraph, END

class LabEquipmentState(TypedDict):
    accessory_id: str
    is_verified: bool
    compliance_docs: list

def validate_accessory(state: LabEquipmentState):
    # Simulate CAD/Spec validation workflow
    state['is_verified'] = state['accessory_id'].startswith('ACC')
    return state

def check_compliance(state: LabEquipmentState):
    # Simulate regulatory/material check logic
    state['compliance_docs'] = ['ISO_9001', 'Material_Safety_Data'] if state['is_verified'] else []
    return state

graph = StateGraph(LabEquipmentState)
graph.add_node('validate', validate_accessory)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()