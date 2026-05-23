from typing import TypedDict
from langgraph.graph import StateGraph, END

class AntisepticState(TypedDict):
    product_name: str
    active_ingredients: list
    concentration: float
    is_compliant: bool

def validate_composition(state: AntisepticState):
    # Business logic for verifying antiseptic concentration safety
    state['is_compliant'] = state['concentration'] > 0.05
    return state

def check_regulatory_status(state: AntisepticState):
    # Check against drug manufacturing databases
    return state

graph = StateGraph(AntisepticState)
graph.add_node('validate', validate_composition)
graph.add_node('compliance', check_regulatory_status)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
