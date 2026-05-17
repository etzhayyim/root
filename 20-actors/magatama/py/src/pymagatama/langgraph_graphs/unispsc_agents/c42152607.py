from typing import TypedDict, Annotated
import operator
from langgraph.graph import StateGraph, END

class DentalRingState(TypedDict):
    spec_data: dict
    validation_errors: Annotated[list, operator.add]
    is_approved: bool

def validate_material(state: DentalRingState):
    errors = []
    if 'material' not in state['spec_data']:
        errors.append('Missing material specification')
    return {'validation_errors': errors}

def check_compliance(state: DentalRingState):
    is_valid = len(state['validation_errors']) == 0
    return {'is_approved': is_valid}

graph = StateGraph(DentalRingState)
graph.add_node('validate_material', validate_material)
graph.add_node('check_compliance', check_compliance)
graph.set_entry_point('validate_material')
graph.add_edge('validate_material', 'check_compliance')
graph.add_edge('check_compliance', END)
graph = graph.compile()