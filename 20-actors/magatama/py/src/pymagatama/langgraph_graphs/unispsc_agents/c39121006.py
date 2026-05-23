from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PowerProcurementState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_specs(state: PowerProcurementState):
    errors = []
    if not state['spec_data'].get('safety_cert'): errors.append('Missing safety cert')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def route_by_compliance(state: PowerProcurementState):
    return 'compliant' if state['is_compliant'] else 'manual_review'

graph = StateGraph(PowerProcurementState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_compliance, {'compliant': END, 'manual_review': END})
graph.compile()
