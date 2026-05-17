from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ChairSpecState(TypedDict):
    material: str
    max_load: float
    safety_compliant: bool

def validate_load(state: ChairSpecState):
    state['safety_compliant'] = state['max_load'] >= 120
    return state

def check_compliance(state: ChairSpecState):
    return 'compliant' if state['safety_compliant'] else 'non_compliant'

graph = StateGraph(ChairSpecState)
graph.add_node('validation', validate_load)
graph.set_entry_point('validation')
graph.add_edge('validation', END)
graph = graph.compile()