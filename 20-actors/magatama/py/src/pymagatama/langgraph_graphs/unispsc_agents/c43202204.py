from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class RingerState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_approved: bool

def validate_specs(state: RingerState):
    errors = []
    if 'voltage' not in state['spec_data']:
        errors.append('Missing voltage rating')
    if 'decibels' not in state['spec_data']:
        errors.append('Missing acoustic output level')
    return {'validation_errors': errors, 'is_approved': len(errors) == 0}

graph = StateGraph(RingerState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()