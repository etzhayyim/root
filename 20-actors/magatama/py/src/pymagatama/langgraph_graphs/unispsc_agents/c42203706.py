from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcessingState(TypedDict):
    chemical_data: dict
    validation_errors: List[str]
    is_approved: bool

def validate_safety_data(state: ProcessingState):
    errors = []
    if 'msds' not in state['chemical_data']:
        errors.append('Missing MSDS')
    return {'validation_errors': errors}

def approval_check(state: ProcessingState):
    return {'is_approved': len(state['validation_errors']) == 0}

graph = StateGraph(ProcessingState)
graph.add_node('validate', validate_safety_data)
graph.add_node('approve', approval_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()
