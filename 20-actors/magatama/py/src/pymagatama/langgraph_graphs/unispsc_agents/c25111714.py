from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class CraftState(TypedDict):
    specs: dict
    validation_errors: List[str]
    approved: bool

def validate_hull_spec(state: CraftState):
    metrics = state['specs']
    errors = []
    if metrics.get('load_capacity', 0) < 5:
        errors.append('Load capacity below utility threshold.')
    return {'validation_errors': errors}

def security_clearance(state: CraftState):
    # Simulated dual-use export check
    return {'approved': len(state['validation_errors']) == 0}

graph = StateGraph(CraftState)
graph.add_node('validate', validate_hull_spec)
graph.add_node('security', security_clearance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'security')
graph.add_edge('security', END)
graph = graph.compile()