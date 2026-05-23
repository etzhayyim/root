from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class RailSpecState(TypedDict):
    material: str
    load_capacity: float
    length: float
    is_compliant: bool
    validation_errors: List[str]

def validate_specs(state: RailSpecState):
    errors = []
    if state['load_capacity'] <= 0:
        errors.append('Invalid load capacity')
    if not state['material']:
        errors.append('Material missing')

    return {'is_compliant': len(errors) == 0, 'validation_errors': errors}

def route_by_compliance(state: RailSpecState):
    return 'valid' if state['is_compliant'] else 'invalid'

graph = StateGraph(RailSpecState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()
