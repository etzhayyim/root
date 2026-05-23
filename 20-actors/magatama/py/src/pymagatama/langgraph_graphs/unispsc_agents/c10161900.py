from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class LivestockState(TypedDict):
    animal_id: str
    health_status: str
    quarantine_cleared: bool
    log: List[str]

def validate_health(state: LivestockState) -> LivestockState:
    state['health_status'] = 'verified' if state.get('health_status') == 'healthy' else 'flagged'
    state['log'].append('Health validation completed')
    return state

def check_quarantine(state: LivestockState) -> LivestockState:
    state['quarantine_cleared'] = True
    state['log'].append('Quarantine check passed')
    return state

graph = StateGraph(LivestockState)
graph.add_node('validate', validate_health)
graph.add_node('quarantine', check_quarantine)
graph.set_entry_point('validate')
graph.add_edge('validate', 'quarantine')
graph.add_edge('quarantine', END)
graph = graph.compile()
