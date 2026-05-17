from typing import TypedDict
from langgraph.graph import StateGraph, END

class OfficeSupplyState(TypedDict):
    item_name: str
    specs: dict
    approved: bool

def validate_specs(state: OfficeSupplyState):
    # Simulate CAD or spec validation
    state['approved'] = 'angle_range' in state['specs'] and 'material' in state['specs']
    return state

graph = StateGraph(OfficeSupplyState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()