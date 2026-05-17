from typing import TypedDict
from langgraph.graph import StateGraph, END

class SuctionPumpState(TypedDict):
    spec: dict
    validation_errors: list
    is_compliant: bool

def validate_specs(state: SuctionPumpState):
    errors = []
    if 'iso_13485_certification' not in state['spec']: errors.append('Missing ISO 13485')
    if state['spec'].get('suction_capacity_lpm', 0) < 20: errors.append('Insufficient capacity')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

graph = StateGraph(SuctionPumpState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()