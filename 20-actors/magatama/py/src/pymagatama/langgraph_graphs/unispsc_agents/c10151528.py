from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class LivestockState(TypedDict):
    animal_id: str
    health_status: str
    quarantine_verified: bool
    transit_log: List[str]

def check_health(state: LivestockState) -> LivestockState:
    state['health_status'] = 'CLEARED' if state.get('health_status') == 'pending' else 'CHECKED'
    return state

def verify_quarantine(state: LivestockState) -> LivestockState:
    state['quarantine_verified'] = True
    state['transit_log'].append('Quarantine verified')
    return state

graph = StateGraph(LivestockState)
graph.add_node('check_health', check_health)
graph.add_node('verify_quarantine', verify_quarantine)
graph.add_edge('check_health', 'verify_quarantine')
graph.add_edge('verify_quarantine', END)
graph.set_entry_point('check_health')

compiled_graph = graph.compile()