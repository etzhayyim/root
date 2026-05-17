from typing import TypedDict
from langgraph.graph import StateGraph, END

class BloodTubeState(TypedDict):
    tube_id: str
    volume_ml: float
    is_sterile: bool
    passed_inspection: bool

def validate_tube(state: BloodTubeState):
    state['passed_inspection'] = state['is_sterile'] and (state['volume_ml'] > 0)
    return state

graph = StateGraph(BloodTubeState)
graph.add_node('validate', validate_tube)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()