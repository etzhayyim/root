from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class FlangeState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_approved: bool

def validate_standards(state: FlangeState):
    errors = []
    if 'pressure_class' not in state['spec_data']: errors.append('Missing pressure class')
    return {'validation_errors': errors}

def final_check(state: FlangeState):
    approved = len(state['validation_errors']) == 0
    return {'is_approved': approved}

graph = StateGraph(FlangeState)
graph.add_node('validate', validate_standards)
graph.add_node('check', final_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'check')
graph.add_edge('check', END)
graph = graph.compile()
