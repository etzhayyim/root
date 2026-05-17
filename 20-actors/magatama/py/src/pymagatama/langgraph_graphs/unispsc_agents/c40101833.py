from typing import TypedDict
from langgraph.graph import StateGraph, END

class IgnitorState(TypedDict):
    part_number: str
    spec_verified: bool
    safety_check_passed: bool

def validate_ignitor(state: IgnitorState):
    state['spec_verified'] = True if state.get('part_number') else False
    return {'spec_verified': state['spec_verified']}

def safety_routing(state: IgnitorState):
    state['safety_check_passed'] = True
    return 'END'

graph = StateGraph(IgnitorState)
graph.add_node('validate', validate_ignitor)
graph.add_node('safety', safety_routing)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()