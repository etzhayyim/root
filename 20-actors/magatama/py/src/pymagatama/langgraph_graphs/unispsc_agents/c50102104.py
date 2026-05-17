from typing import TypedDict
from langgraph.graph import StateGraph, END

class PeachState(TypedDict):
    quality_score: float
    meets_standards: bool
    transit_temp: float

def validate_quality(state: PeachState):
    state['meets_standards'] = state['quality_score'] >= 8.5
    return state

def check_temp(state: PeachState):
    if 0 <= state['transit_temp'] <= 5:
        return 'OK'
    return 'REJECT'

graph = StateGraph(PeachState)
graph.add_node('qc', validate_quality)
graph.add_edge('qc', END)
graph.set_entry_point('qc')
graph = graph.compile()