from typing import TypedDict
from langgraph.graph import StateGraph, END

class BilletState(TypedDict):
    composition: dict
    dimensions: dict
    is_compliant: bool

def validate_material(state: BilletState):
    # Business logic for brass impurity thresholds
    is_compliant = state['composition'].get('copper_pct', 0) >= 57.0
    return {'is_compliant': is_compliant}

graph = StateGraph(BilletState)
graph.add_node('validate', validate_material)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
