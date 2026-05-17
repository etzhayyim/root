from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ActuatorState(TypedDict):
    specs: dict
    validation_errors: List[str]
    is_approved: bool

def validate_specs(state: ActuatorState):
    errors = []
    if state['specs'].get('force_capacity_n', 0) <= 0:
        errors.append('Invalid force capacity')
    return {'validation_errors': errors}

def routing_logic(state: ActuatorState):
    return 'approved' if not state['validation_errors'] else 'rejected'

graph = StateGraph(ActuatorState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()