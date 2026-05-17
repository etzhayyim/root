from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class LimeState(TypedDict):
    origin: str
    quality_score: float
    storage_temp: float
    is_compliant: bool

def validate_quality(state: LimeState):
    state['is_compliant'] = 0 <= state['storage_temp'] <= 5 and state['quality_score'] > 0.8
    return state

def route_by_compliance(state: LimeState):
    return 'process_success' if state['is_compliant'] else 'reject_shipment'

graph = StateGraph(LimeState)
graph.add_node('validate', validate_quality)
graph.add_edge('validate', END)
graph.set_entry_point('validate')