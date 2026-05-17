from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
import operator

class BearingProcurementState(TypedDict):
    spec_data: dict
    validation_errors: Annotated[List[str], operator.add]
    is_compliant: bool

def validate_bearing_specs(state: BearingProcurementState):
    errors = []
    specs = state['spec_data']
    if specs.get('load_rating_dynamic', 0) < 1000:
        errors.append('Insufficient dynamic load rating for industrial robotics.')
    if not specs.get('iso_tolerance_class'):
        errors.append('Missing ISO tolerance class.')
    return {'validation_errors': errors}

def determine_compliance(state: BearingProcurementState):
    return {'is_compliant': len(state['validation_errors']) == 0}

graph = StateGraph(BearingProcurementState)
graph.add_node('validate', validate_bearing_specs)
graph.add_node('check_compliance', determine_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'check_compliance')
graph.add_edge('check_compliance', END)
graph = graph.compile()