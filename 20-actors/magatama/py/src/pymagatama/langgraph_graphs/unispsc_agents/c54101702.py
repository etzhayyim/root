from typing import TypedDict
from langgraph.graph import StateGraph, END

class PunchState(TypedDict):
    material_grade: str
    hardness: float
    passed_inspection: bool

def validate_hardness(state: PunchState):
    state['passed_inspection'] = state['hardness'] >= 55.0
    return state

graph = StateGraph(PunchState)
graph.add_node('validate', validate_hardness)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
