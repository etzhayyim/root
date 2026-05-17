from typing import TypedDict
from langgraph.graph import StateGraph, END

class RocketState(TypedDict):
    spec_data: dict
    validation_flags: dict

def validate_propellant(state: RocketState):
    is_valid = state['spec_data'].get('propellant_type') in ['HTPB', 'Composite']
    return {'validation_flags': {'propellant': is_valid}}

def check_compliance(state: RocketState):
    is_compliant = state['spec_data'].get('itar_compliance_status') == 'Verified'
    return {'validation_flags': {'compliance': is_compliant}}

graph = StateGraph(RocketState)
graph.add_node('val_prop', validate_propellant)
graph.add_node('check_comp', check_compliance)
graph.set_entry_point('val_prop')
graph.add_edge('val_prop', 'check_comp')
graph.add_edge('check_comp', END)
graph = graph.compile()