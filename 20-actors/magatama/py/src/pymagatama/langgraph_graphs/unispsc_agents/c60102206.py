from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class PhonicsState(TypedDict):
    content: str
    validation_errors: List[str]
    spec_compliance: bool

def validate_safety(state: PhonicsState):
    errors = []
    if 'non-toxic' not in state['content'].lower():
        errors.append('Missing non-toxic certification')
    return {**state, 'validation_errors': errors}

def check_compliance(state: PhonicsState):
    return {**state, 'spec_compliance': len(state['validation_errors']) == 0}

graph = StateGraph(PhonicsState)
graph.add_node('safety', validate_safety)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('safety')
graph.add_edge('safety', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()