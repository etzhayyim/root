from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CargoHeliState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_cleared: bool

def validate_payload(state: CargoHeliState):
    capacity = state['spec_data'].get('payload', 0)
    if capacity <= 0:
        state['validation_errors'].append('Invalid payload capacity')
    return {'is_cleared': len(state['validation_errors']) == 0}

def export_compliance_check(state: CargoHeliState):
    if 'export_license' not in state['spec_data']:
        state['validation_errors'].append('Missing export license for dual-use item')
    return {'is_cleared': len(state['validation_errors']) == 0}

graph = StateGraph(CargoHeliState)
graph.add_node('validate_payload', validate_payload)
graph.add_node('export_check', export_compliance_check)
graph.set_entry_point('validate_payload')
graph.add_edge('validate_payload', 'export_check')
graph.add_edge('export_check', END)
graph = graph.compile()
