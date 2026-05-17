from typing import TypedDict
from langgraph.graph import StateGraph, END

class RehabEquipmentState(TypedDict):
    item_name: str
    specs: dict
    approved: bool

def validate_specs(state: RehabEquipmentState):
    is_safe = state['specs'].get('weight_capacity', 0) > 100
    return {'approved': is_safe}

def build_graph():
    graph = StateGraph(RehabEquipmentState)
    graph.add_node('validate', validate_specs)
    graph.set_entry_point('validate')
    graph.add_edge('validate', END)
    return graph.compile()

graph = build_graph()