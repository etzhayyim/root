from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class LivestockState(TypedDict):
    animal_id: str
    health_status: str
    quarantine_verified: bool
    transport_logs: List[str]

def inspect_health(state: LivestockState) -> LivestockState:
    # Logic for health assessment
    state['health_status'] = 'certified'
    return state

def verify_quarantine(state: LivestockState) -> LivestockState:
    # Logic for quarantine compliance check
    state['quarantine_verified'] = True
    return state

def finalize_shipping(state: LivestockState) -> LivestockState:
    # Logic for transport approval
    state['transport_logs'].append('Shipping approved')
    return state

graph = StateGraph(LivestockState)
graph.add_node('inspect', inspect_health)
graph.add_node('quarantine', verify_quarantine)
graph.add_node('shipping', finalize_shipping)
graph.add_edge('inspect', 'quarantine')
graph.add_edge('quarantine', 'shipping')
graph.add_edge('shipping', END)
graph.set_entry_point('inspect')
graph = graph.compile()
