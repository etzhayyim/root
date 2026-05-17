from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class WireProcurementState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_spec(state: WireProcurementState):
    errors = []
    if state['spec_data'].get('temp_rating', 0) < 200:
        errors.append('Temperature rating insufficient for Kaptan wire applications.')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def route_by_compliance(state: WireProcurementState):
    return 'compliant' if state['is_compliant'] else 'flag_review'

graph = StateGraph(WireProcurementState)
graph.add_node('validate', validate_spec)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_compliance, {'compliant': END, 'flag_review': END})
graph.compile()