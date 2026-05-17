from typing import TypedDict
from langgraph.graph import StateGraph, END
class CampingTableState(TypedDict):
    spec: dict
    approved: bool
def validate_load_capacity(state: CampingTableState) -> CampingTableState:
    limit = state['spec'].get('load_capacity_kg', 0)
    state['approved'] = limit > 0 and limit < 200
    return state
def check_dimensions(state: CampingTableState) -> CampingTableState:
    dims = state['spec'].get('folded_dimensions', '')
    if not dims: state['approved'] = False
    return state
graph = StateGraph(CampingTableState)
graph.add_node('validate_load', validate_load_capacity)
graph.add_node('check_dims', check_dimensions)
graph.set_entry_point('validate_load')
graph.add_edge('validate_load', 'check_dims')
graph.add_edge('check_dims', END)
graph = graph.compile()