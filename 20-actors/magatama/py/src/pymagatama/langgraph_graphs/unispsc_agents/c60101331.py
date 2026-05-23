import operator
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, END

class State(TypedDict):
    flashcard_data: dict
    validation_errors: Annotated[list, operator.add]
    is_approved: bool

def validate_data(state: State):
    errors = []
    if 'state_facts' not in state['flashcard_data']:
        errors.append('Missing state facts')
    return {'validation_errors': errors}

def check_quality(state: State):
    approved = len(state['validation_errors']) == 0
    return {'is_approved': approved}

graph = StateGraph(State)
graph.add_node('validate', validate_data)
graph.add_node('quality_check', check_quality)
graph.add_edge('validate', 'quality_check')
graph.add_edge('quality_check', END)
graph.set_entry_point('validate')
graph = graph.compile()
