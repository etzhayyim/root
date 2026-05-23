from typing import TypedDict
from langgraph.graph import StateGraph, END

class QualityState(TypedDict):
    fruit_type: str
    freshness_score: float
    inspection_passed: bool

def validate_quality(state: QualityState) -> QualityState:
    if state['freshness_score'] > 0.8:
        state['inspection_passed'] = True
    return state

def run_checks(state: QualityState) -> str:
    return 'pass' if state['inspection_passed'] else 'fail'

graph = StateGraph(QualityState)
graph.add_node('validation', validate_quality)
graph.set_entry_point('validation')
graph.add_edge('validation', END)
graph.compile()
