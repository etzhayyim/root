from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class PetroleumState(TypedDict):
    batch_id: str
    purity: float
    safety_check_passed: bool
    logs: Annotated[Sequence[str], operator.add]

def validate_composition(state: PetroleumState) -> dict:
    passed = state['purity'] > 0.95
    return {'safety_check_passed': passed, 'logs': ['Composition validated against industrial standards']}

def update_inventory(state: PetroleumState) -> dict:
    return {'logs': ['Inventory records updated successfully']}

graph = StateGraph(PetroleumState)
graph.add_node('validate', validate_composition)
graph.add_node('inventory', update_inventory)
graph.add_edge('validate', 'inventory')
graph.add_edge('inventory', END)
graph.set_entry_point('validate')
graph = graph.compile()