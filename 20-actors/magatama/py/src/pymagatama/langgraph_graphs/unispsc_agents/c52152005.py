from typing import TypedDict
from langgraph.graph import StateGraph, END

class SaucerState(TypedDict):
    material: str
    food_safety_cert: bool
    dimensions: dict
    approved: bool

def validate_material(state: SaucerState):
    # Simulate material compliance check
    return {'approved': state['food_safety_cert'] and state['material'] in ['Ceramic', 'Glass', 'Porcelain']}

def check_dimensions(state: SaucerState):
    # Logic to ensure standard saucer size
    return {'approved': state['approved'] and state['dimensions'].get('diameter', 0) > 10}

graph = StateGraph(SaucerState)
graph.add_node('validate_material', validate_material)
graph.add_node('check_dimensions', check_dimensions)
graph.set_entry_point('validate_material')
graph.add_edge('validate_material', 'check_dimensions')
graph.add_edge('check_dimensions', END)

compiled_graph = graph.compile()
