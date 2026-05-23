from typing import TypedDict
from langgraph.graph import StateGraph, END

class DrugState(TypedDict):
    batch_id: str
    purity_level: float
    compliant: bool

def validate_quality(state: DrugState) -> DrugState:
    state['compliant'] = state['purity_level'] >= 99.0
    return state

def check_compliance(state: DrugState) -> str:
    return 'APPROVED' if state['compliant'] else 'REJECTED'

graph = StateGraph(DrugState)
graph.add_node('validation', validate_quality)
graph.set_entry_point('validation')
graph.add_edge('validation', END)
graph = graph.compile()
