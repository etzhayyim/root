from typing import TypedDict
from langgraph.graph import StateGraph, END

class FoilState(TypedDict):
    thickness: float
    grade: str
    mtc_attached: bool
    approved: bool

def validate_specs(state: FoilState):
    if state['thickness'] < 0.01: return {'approved': False}
    return {'approved': state['mtc_attached']}

graph = StateGraph(FoilState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()