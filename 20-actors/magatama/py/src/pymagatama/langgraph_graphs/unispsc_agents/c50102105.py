from langgraph.graph import StateGraph, END
from typing import TypedDict
class PlumProcurementState(TypedDict):
    brix_level: float
    shelf_life_days: int
    is_compliant: bool
def validate_quality(state: PlumProcurementState):
    state['is_compliant'] = state['brix_level'] >= 12.0 and state['shelf_life_days'] > 5
    return state
graph = StateGraph(PlumProcurementState)
graph.add_node('validate', validate_quality)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()