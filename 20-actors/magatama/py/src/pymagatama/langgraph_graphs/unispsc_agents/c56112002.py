from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class WorkSurfaceState(TypedDict):
    specs: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_ergonomic_standards(state: WorkSurfaceState):
    errors = []
    if state['specs'].get('load_capacity', 0) < 50:
        errors.append('Load capacity below BIFMA minimum standards.')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def route_to_procurement(state: WorkSurfaceState):
    return 'approved' if state['is_compliant'] else 'rejected'

graph = StateGraph(WorkSurfaceState)
graph.add_node('validate', validate_ergonomic_standards)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()