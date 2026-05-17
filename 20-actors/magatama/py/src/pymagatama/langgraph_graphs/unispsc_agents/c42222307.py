from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class TransfusionSystemState(TypedDict):
    specs: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_specs(state: TransfusionSystemState):
    required = ['ISO_13485_certification', 'thermal_precision_range']
    errors = [field for field in required if field not in state['specs']]
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def route_by_compliance(state: TransfusionSystemState):
    return 'compliant' if state['is_compliant'] else 'manual_review'

graph = StateGraph(TransfusionSystemState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_compliance, {'compliant': END, 'manual_review': END})
graph = graph.compile()