from typing import TypedDict
from langgraph.graph import StateGraph, END

class PressState(TypedDict):
    tonnage: float
    safety_check: bool
    compliant: bool

def validate_specs(state: PressState):
    state['compliant'] = state['tonnage'] > 0 and state['safety_check']
    return state

def safety_audit(state: PressState):
    return {'safety_check': True}

graph = StateGraph(PressState)
graph.add_node('audit', safety_audit)
graph.add_node('validate', validate_specs)
graph.set_entry_point('audit')
graph.add_edge('audit', 'validate')
graph.add_edge('validate', END)
graph = graph.compile()
