from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class RailState(TypedDict):
    specs: dict
    validation_passed: bool
    log: List[str]

def validate_material(state: RailState):
    alloy = state['specs'].get('alloy', 'Unknown')
    is_valid = alloy in ['6061-T6', '6063-T5']
    return {'validation_passed': is_valid, 'log': [f'Alloy {alloy} validation: {is_valid}']}

def check_dimensions(state: RailState):
    length = state['specs'].get('length', 0)
    status = length > 0
    return {'validation_passed': status, 'log': [f'Dimension check: {status}']}

graph = StateGraph(RailState)
graph.add_node('material', validate_material)
graph.add_node('dimensions', check_dimensions)
graph.add_edge('material', 'dimensions')
graph.add_edge('dimensions', END)
graph.set_entry_point('material')
graph = graph.compile()