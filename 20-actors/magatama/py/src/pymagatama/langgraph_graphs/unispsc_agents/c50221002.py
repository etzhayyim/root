from typing import TypedDict
from langgraph.graph import StateGraph, END

class PulseFlourState(TypedDict):
    moisture_level: float
    purity_certified: bool
    approved: bool

def validate_moisture(state: PulseFlourState):
    state['approved'] = state['moisture_level'] < 14.0
    return state

workflow = StateGraph(PulseFlourState)
workflow.add_node('moisture_validation', validate_moisture)
workflow.set_entry_point('moisture_validation')
workflow.add_edge('moisture_validation', END)
graph = workflow.compile()