from typing import TypedDict
from langgraph.graph import StateGraph, END

class CopperRodState(TypedDict):
    purity: float
    diameter_mm: float
    compliance: bool

def validate_specs(state: CopperRodState):
    state['compliance'] = state['purity'] >= 99.9 and state['diameter_mm'] > 0
    return 'valid' if state['compliance'] else 'invalid'

graph = StateGraph(CopperRodState)
graph.add_node('validation', validate_specs)
graph.set_entry_point('validation')
graph.add_edge('validation', END)
graph = graph.compile()
