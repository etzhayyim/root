from typing import TypedDict, List, Annotated
from langgraph.graph import StateGraph, END

class LivestockState(TypedDict):
    animal_id: str
    health_status: str
    quarantine_clearance: bool
    history: List[str]

def validate_health(state: LivestockState):
    # Simulate health verification check
    return {'health_status': 'verified' if state['health_status'] == 'healthy' else 'rejected'}

def check_quarantine(state: LivestockState):
    # Simulate quarantine logic
    return {'quarantine_clearance': True}

graph = StateGraph(LivestockState)
graph.add_node('health', validate_health)
graph.add_node('quarantine', check_quarantine)
graph.set_entry_point('health')
graph.add_edge('health', 'quarantine')
graph.add_edge('quarantine', END)
graph = graph.compile()