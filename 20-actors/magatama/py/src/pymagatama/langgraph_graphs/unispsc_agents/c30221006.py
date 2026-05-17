from typing import TypedDict
from langgraph.graph import StateGraph, END

class CanteenState(TypedDict):
    specs: dict
    approved: bool

def validate_material(state: CanteenState):
    is_bpa_free = state['specs'].get('bpa_free', False)
    return {'approved': is_bpa_free}

def check_integrity(state: CanteenState):
    passed = state['specs'].get('leak_test_passed', False)
    return {'approved': state['approved'] and passed}

graph = StateGraph(CanteenState)
graph.add_node('material_check', validate_material)
graph.add_node('integrity_check', check_integrity)
graph.set_entry_point('material_check')
graph.add_edge('material_check', 'integrity_check')
graph.add_edge('integrity_check', END)
graph = graph.compile()