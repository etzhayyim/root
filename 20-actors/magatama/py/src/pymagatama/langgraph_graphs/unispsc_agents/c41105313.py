from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    spec_data: dict
    validation_status: bool
    error_log: list

def validate_spec(state: ProcurementState):
    required = ['Material-Composition', 'Lot-Traceability-Number']
    missing = [f for f in required if f not in state['spec_data']]
    return {'validation_status': len(missing) == 0, 'error_log': missing}

def route_by_validation(state: ProcurementState):
    return 'validate' if not state.get('validation_status') else END

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_spec)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()