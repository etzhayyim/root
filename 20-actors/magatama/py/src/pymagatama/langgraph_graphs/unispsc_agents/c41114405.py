from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class RainfallState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    approved: bool

def validate_specs(state: RainfallState):
    errors = []
    if 'IP_rating' not in state['spec_data'] or int(state['spec_data']['IP_rating']) < 65:
        errors.append('Invalid IP rating for outdoor use.')
    return {'validation_errors': errors}

def check_approval(state: RainfallState):
    return {'approved': len(state['validation_errors']) == 0}

graph = StateGraph(RainfallState)
graph.add_node('validate', validate_specs)
graph.add_node('approval', check_approval)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approval')
graph.add_edge('approval', END)
graph = graph.compile()
