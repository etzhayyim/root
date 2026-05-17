from typing import TypedDict
from langgraph.graph import StateGraph, END

class LimeProcurementState(TypedDict):
    purity_level: float
    moisture_content: float
    compliant: bool

def validate_composition(state: LimeProcurementState):
    state['compliant'] = state['purity_level'] > 90.0 and state['moisture_content'] < 2.0
    return state

graph = StateGraph(LimeProcurementState)
graph.add_node('validate', validate_composition)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()