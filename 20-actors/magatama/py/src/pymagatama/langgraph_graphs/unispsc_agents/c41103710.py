from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class EquipmentState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    approved: bool

def validate_specs(state: EquipmentState):
    errors = []
    if 'temperature_range_celsius' not in state['spec_data']:
        errors.append('Missing temperature capacity')
    return {'validation_errors': errors}

def decision_node(state: EquipmentState):
    if not state['validation_errors']:
        return 'approved'
    return 'rejected'

graph = StateGraph(EquipmentState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()
