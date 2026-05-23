from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PomeFruitState(TypedDict):
    fruit_type: str
    quality_score: float
    temp_log: List[float]
    is_compliant: bool

def validate_freshness(state: PomeFruitState):
    state['is_compliant'] = all(t < 5.0 for t in state['temp_log']) and state['quality_score'] > 0.8
    return state

def route_procurement(state: PomeFruitState):
    return 'compliant' if state['is_compliant'] else 'reject'

graph = StateGraph(PomeFruitState)
graph.add_node('validation', validate_freshness)
graph.add_edge('validation', END)
graph.set_entry_point('validation')
graph = graph.compile()
