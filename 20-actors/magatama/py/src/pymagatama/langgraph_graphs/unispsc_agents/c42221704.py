from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class PressureBagState(TypedDict):
    spec_data: dict
    valid: bool
    errors: List[str]

def validate_pressure_compliance(state: PressureBagState):
    pressure = state['spec_data'].get('pressure_rating_mmhg', 0)
    if not (200 <= pressure <= 400):
        return {'valid': False, 'errors': ['Pressure rating out of range']}
    return {'valid': True}

def safety_compliance_check(state: PressureBagState):
    if not state.get('spec_data', {}).get('iso_13485_certified', False):
        return {'errors': ['Missing ISO certification']}
    return {'valid': True}

graph = StateGraph(PressureBagState)
graph.add_node('validate_pressure', validate_pressure_compliance)
graph.add_node('safety_check', safety_compliance_check)
graph.set_entry_point('validate_pressure')
graph.add_edge('validate_pressure', 'safety_check')
graph.add_edge('safety_check', END)
graph = graph.compile()
