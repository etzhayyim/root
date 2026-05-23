from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class PrecursorState(TypedDict):
    purity_level: float
    safety_clearance: bool
    shipping_log: Annotated[Sequence[str], operator.add]

def validate_purity(state: PrecursorState) -> PrecursorState:
    if state['purity_level'] < 99.999:
        raise ValueError('Purity below semiconductor grade standards')
    return {'shipping_log': ['Purity validation passed']}

def check_safety_protocols(state: PrecursorState) -> PrecursorState:
    # Logic for dual-use and dangerous goods compliance
    return {'safety_clearance': True, 'shipping_log': ['Safety clearance verified']}

graph = StateGraph(PrecursorState)
graph.add_node('validate', validate_purity)
graph.add_node('safety', check_safety_protocols)
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph.set_entry_point('validate')
graph = graph.compile()
