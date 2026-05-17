from typing import TypedDict
from langgraph.graph import StateGraph, END

class State(TypedDict):
    spec_data: dict
    approved: bool

def validate_safety_standards(state: State):
    reqs = state['spec_data'].get('safety_compliance', [])
    is_approved = 'ISO_13485' in reqs
    return {'approved': is_approved}

def final_check(state: State):
    return {'approved': state.get('approved', False)}

graph = StateGraph(State)
graph.add_node('safety_check', validate_safety_standards)
graph.add_node('final_approval', final_check)
graph.set_entry_point('safety_check')
graph.add_edge('safety_check', 'final_approval')
graph.add_edge('final_approval', END)
app = graph.compile()