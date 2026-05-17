from typing import TypedDict
from langgraph.graph import StateGraph, END

class NapkinState(TypedDict):
    material: str
    ply: int
    quantity: int
    compliant: bool

def validate_napkins(state: NapkinState):
    state['compliant'] = state['material'] in ['paper', 'cotton', 'linen'] and state['ply'] > 0
    return state

def route_procurement(state: NapkinState):
    return 'process' if state['compliant'] else END

graph = StateGraph(NapkinState)
graph.add_node('validate', validate_napkins)
graph.add_node('process', lambda s: s)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_procurement)
graph.add_edge('process', END)
graph = graph.compile()