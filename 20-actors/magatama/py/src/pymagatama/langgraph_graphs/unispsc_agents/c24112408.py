from typing import TypedDict
from langgraph.graph import StateGraph, END
class BoxState(TypedDict):
    surface_resistance: float
    is_rohs_compliant: bool
    approved: bool
def validate_esd_properties(state: BoxState):
    res = state['surface_resistance']
    valid = (1e5 <= res <= 1e9) and state['is_rohs_compliant']
    return {'approved': valid}
graph = StateGraph(BoxState)
graph.add_node('validate', validate_esd_properties)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
