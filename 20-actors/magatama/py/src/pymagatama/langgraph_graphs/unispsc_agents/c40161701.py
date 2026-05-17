from typing import TypedDict
from langgraph.graph import StateGraph, END

class CentrifugeState(TypedDict):
    rpm: int
    certified: bool
    safety_check: bool

def validate_specs(state: CentrifugeState):
    state['safety_check'] = state['rpm'] < 50000 and state['certified']
    return state

def route_by_safety(state: CentrifugeState):
    return 'process' if state['safety_check'] else 'reject'

graph = StateGraph(CentrifugeState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')
app = graph.compile()