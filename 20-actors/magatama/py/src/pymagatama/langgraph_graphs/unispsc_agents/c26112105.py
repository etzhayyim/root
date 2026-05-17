from typing import TypedDict
from langgraph.graph import StateGraph, END

class BrakingSystemState(TypedDict):
    spec_data: dict
    validation_checks: list
    is_compliant: bool

def validate_tech_specs(state: BrakingSystemState):
    checks = []
    if state['spec_data'].get('torque_nm') and state['spec_data'].get('voltage'):
        checks.append('Technical specs valid')
    return {'validation_checks': checks, 'is_compliant': True}

def approve_procurement(state: BrakingSystemState):
    return {'is_compliant': True}

graph = StateGraph(BrakingSystemState)
graph.add_node('validate', validate_tech_specs)
graph.add_node('approval', approve_procurement)
graph.add_edge('validate', 'approval')
graph.add_edge('approval', END)
graph.set_entry_point('validate')
graph = graph.compile()