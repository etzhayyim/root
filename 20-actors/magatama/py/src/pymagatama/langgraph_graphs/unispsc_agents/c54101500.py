from typing import TypedDict
from langgraph.graph import StateGraph, END

class JewelryState(TypedDict):
    item_details: dict
    auth_verified: bool
    transit_secure: bool

def verify_authenticity(state: JewelryState):
    state['auth_verified'] = 'certificate_id' in state['item_details']
    return state

def check_security(state: JewelryState):
    state['transit_secure'] = state['item_details'].get('value', 0) < 50000
    return state

graph = StateGraph(JewelryState)
graph.add_node('verify', verify_authenticity)
graph.add_node('security', check_security)
graph.set_entry_point('verify')
graph.add_edge('verify', 'security')
graph.add_edge('security', END)
graph = graph.compile()