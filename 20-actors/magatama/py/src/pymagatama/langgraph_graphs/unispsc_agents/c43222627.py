from typing import TypedDict
from langgraph.graph import StateGraph, END

class ISDNState(TypedDict):
    device_specs: dict
    is_compliant: bool

def validate_isdn_specs(state: ISDNState):
    # Simulate validation logic for ISDN access devices
    required_fields = ['interface_protocol', 'transmission_rate']
    is_valid = all(field in state['device_specs'] for field in required_fields)
    return {'is_compliant': is_valid}

def route_by_compliance(state: ISDNState):
    return 'valid' if state['is_compliant'] else 'invalid'

graph = StateGraph(ISDNState)
graph.add_node('validator', validate_isdn_specs)
graph.set_entry_point('validator')
graph.add_edge('validator', END)
graph.compile()