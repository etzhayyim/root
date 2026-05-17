from typing import TypedDict
from langgraph.graph import StateGraph, END

class PhonebookState(TypedDict):
    data: dict
    validation_errors: list
    is_approved: bool

def validate_phonebook_schema(state: PhonebookState):
    errors = []
    if 'db_connector' not in state['data']: errors.append('Missing DB connector')
    return {'validation_errors': errors}

def approval_check(state: PhonebookState):
    return {'is_approved': len(state['validation_errors']) == 0}

graph = StateGraph(PhonebookState)
graph.add_node('validate', validate_phonebook_schema)
graph.add_node('approval', approval_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approval')
graph.add_edge('approval', END)
graph = graph.compile()