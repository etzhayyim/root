from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class SculptureSupplyState(TypedDict):
    item_name: str
    material: str
    safety_check: bool
    approved: bool

def validate_safety(state: SculptureSupplyState):
    # Simulate material compliance check
    state['safety_check'] = 'toxic' not in state['material'].lower()
    return state

def approve_procurement(state: SculptureSupplyState):
    state['approved'] = state['safety_check']
    return state

graph = StateGraph(SculptureSupplyState)
graph.add_node('validate', validate_safety)
graph.add_node('approve', approve_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()