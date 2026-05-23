from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ShutterState(TypedDict):
    specs: dict
    validation_errors: List[str]
    approved: bool

def validate_specs(state: ShutterState):
    required = ['dimensions', 'fire_rating', 'wind_load']
    errors = [f'Missing {f}' for f in required if f not in state['specs']]
    return {'validation_errors': errors, 'approved': len(errors) == 0}

graph = StateGraph(ShutterState)
graph.add_node('validator', validate_specs)
graph.set_entry_point('validator')
graph.add_edge('validator', END)
graph = graph.compile()
