from typing import TypedDict
from langgraph.graph import StateGraph, END

class FurnitureState(TypedDict):
    item_name: str
    safety_specs: dict
    approved: bool

def validate_safety(state: FurnitureState):
    required = ['flammability', 'toxic_free']
    all_passed = all(state['safety_specs'].get(k) for k in required)
    return {'approved': all_passed}

graph = StateGraph(FurnitureState)
graph.add_node('safety_check', validate_safety)
graph.set_entry_point('safety_check')
graph.add_edge('safety_check', END)
graph = graph.compile()
