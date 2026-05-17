from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ProcurementState(TypedDict):
    commodity: str
    specifications: dict
    approved: bool
    validation_errors: List[str]

def validate_purity(state: ProcurementState):
    errors = []
    if state['specifications'].get('brix', 0) < 10:
        errors.append('Brix level too low')
    return {'validation_errors': errors, 'approved': len(errors) == 0}

def route_by_validation(state: ProcurementState):
    return 'process' if state['approved'] else END

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_purity)
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')
compiled_graph = graph.compile()