from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class GableState(TypedDict):
    specifications: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_structural_integrity(state: GableState):
    # Simulated logic checking for building code standards
    if state['specifications'].get('load_capacity', 0) < 500:
        state['validation_errors'].append('Load capacity below minimum standard')
    return {'is_compliant': len(state['validation_errors']) == 0}

def route_by_compliance(state: GableState):
    return 'compliant' if state['is_compliant'] else 'rejected'

graph = StateGraph(GableState)
graph.add_node('validate', validate_structural_integrity)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_compliance, {'compliant': END, 'rejected': END})
graph = graph.compile()