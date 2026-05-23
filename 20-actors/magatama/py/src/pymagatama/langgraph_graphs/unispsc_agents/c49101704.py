from typing import TypedDict
from langgraph.graph import StateGraph, END

class PlaqueState(TypedDict):
    material: str
    engraving_content: str
    dimensions: dict
    approved: bool

def validate_material(state: PlaqueState):
    allowed = ['brass', 'wood', 'acrylic', 'aluminum']
    return {'approved': state['material'] in allowed}

def process_design(state: PlaqueState):
    # Simulate CAD verification for engraving depth
    return {'approved': True}

graph = StateGraph(PlaqueState)
graph.add_node('validate', validate_material)
graph.add_node('design_check', process_design)
graph.add_edge('validate', 'design_check')
graph.add_edge('design_check', END)
graph.set_entry_point('validate')
graph = graph.compile()
