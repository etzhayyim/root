from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class GasManifoldState(TypedDict):
    specs: dict
    validation_errors: List[str]
    is_approved: bool

def validate_specs(state: GasManifoldState):
    errors = []
    if state['specs'].get('pressure_rating', 0) < 1000:
        errors.append('Insufficient pressure rating for medical standards')
    return {'validation_errors': errors, 'is_approved': len(errors) == 0}

graph = StateGraph(GasManifoldState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()