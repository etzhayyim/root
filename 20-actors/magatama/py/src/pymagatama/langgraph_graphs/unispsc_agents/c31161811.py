from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class SpringWasherState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_approved: bool

def validate_dimensions(state: SpringWasherState):
    errors = []
    if 'hardness' not in state['spec_data']:
        errors.append('Missing hardness rating')
    return {**state, 'validation_errors': errors}

def quality_check(state: SpringWasherState):
    approved = len(state['validation_errors']) == 0
    return {**state, 'is_approved': approved}

graph = StateGraph(SpringWasherState)
graph.add_node('validate', validate_dimensions)
graph.add_node('check', quality_check)
graph.add_edge('validate', 'check')
graph.add_edge('check', END)
graph.set_entry_point('validate')
compiled_graph = graph.compile()