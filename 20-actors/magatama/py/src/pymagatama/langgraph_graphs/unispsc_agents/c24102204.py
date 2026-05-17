from typing import TypedDict
from langgraph.graph import StateGraph, END

class StrappingState(TypedDict):
    spec_data: dict
    validation_log: list
    is_approved: bool

def validate_specs(state: StrappingState):
    log = []
    if state['spec_data'].get('load_capacity', 0) <= 0:
        log.append('Invalid load capacity')
    return {'validation_log': log, 'is_approved': len(log) == 0}

def route_by_validation(state: StrappingState):
    return 'approved' if state['is_approved'] else 'rejected'

graph = StateGraph(StrappingState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()