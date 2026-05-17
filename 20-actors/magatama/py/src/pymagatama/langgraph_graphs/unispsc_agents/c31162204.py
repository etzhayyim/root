from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class RivetState(TypedDict):
    material: str
    specs: dict
    approved: bool

def validate_material(state: RivetState):
    # Business logic for material compliance check
    return {'approved': state['material'] in ['Aluminum', 'Steel', 'Titanium']}

def check_dimensions(state: RivetState):
    # Verify dimension tolerance logic
    return {'approved': state['specs'].get('tolerance', 0.01) <= 0.05}

graph = StateGraph(RivetState)
graph.add_node('validation', validate_material)
graph.add_node('dimensions', check_dimensions)
graph.set_entry_point('validation')
graph.add_edge('validation', 'dimensions')
graph.add_edge('dimensions', END)
graph = graph.compile()