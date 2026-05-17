from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class GrapeState(TypedDict):
    brix: float
    purity_certified: bool
    batch_number: str
    quality_status: str

def validate_quality(state: GrapeState):
    if state['brix'] > 60 and state['purity_certified']:
        return {'quality_status': 'PASS'}
    return {'quality_status': 'FAIL'}

graph = StateGraph(GrapeState)
graph.add_node('validate', validate_quality)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()