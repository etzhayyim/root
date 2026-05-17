from typing import TypedDict
from langgraph.graph import StateGraph, END

class ConcentrateState(TypedDict):
    brix: float
    safety_check: bool
    approved: bool

def validate_brix(state: ConcentrateState):
    state['approved'] = 10.0 <= state['brix'] <= 15.0
    return state

def safety_audit(state: ConcentrateState):
    state['safety_check'] = True
    return state

graph = StateGraph(ConcentrateState)
graph.add_node('validate_brix', validate_brix)
graph.add_node('safety_audit', safety_audit)
graph.set_entry_point('validate_brix')
graph.add_edge('validate_brix', 'safety_audit')
graph.add_edge('safety_audit', END)
graph = graph.compile()