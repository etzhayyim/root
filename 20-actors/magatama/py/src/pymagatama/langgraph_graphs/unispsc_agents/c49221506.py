from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SportMatState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    approved: bool

def validate_safety_compliance(state: SportMatState):
    errors = []
    if 'fire_retardancy' not in state['spec_data']:
        errors.append('Missing fire retardancy certification')
    return {'validation_errors': errors}

def finalize_procurement(state: SportMatState):
    approved = len(state.get('validation_errors', [])) == 0
    return {'approved': approved}

graph = StateGraph(SportMatState)
graph.add_node('validate', validate_safety_compliance)
graph.add_node('finalize', finalize_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()
