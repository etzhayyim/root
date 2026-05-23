from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class KitchenwareState(TypedDict):
    item_name: str
    specs: dict
    approved: bool

def validate_specs(state: KitchenwareState):
    required_fields = ['material', 'gauge']
    state['approved'] = all(k in state['specs'] for k in required_fields)
    return state

def check_food_safety(state: KitchenwareState):
    return state

graph = StateGraph(KitchenwareState)
graph.add_node('validate', validate_specs)
graph.add_node('safety', check_food_safety)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()
