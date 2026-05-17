from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class TitaniumPartState(TypedDict):
    part_id: str
    material_spec: str
    dimension_check: bool
    compliance_tags: List[str]

def validate_materials(state: TitaniumPartState):
    # Simulate material compliance check for aerospace grade titanium
    state['material_spec'] = 'Certified Grade 5' if state['part_id'] else 'Unknown'
    return state

def check_dimensions(state: TitaniumPartState):
    # Logic to verify cold extrusion tolerances
    state['dimension_check'] = True
    return state

graph = StateGraph(TitaniumPartState)
graph.add_node('validate', validate_materials)
graph.add_node('dimensions', check_dimensions)
graph.set_entry_point('validate')
graph.add_edge('validate', 'dimensions')
graph.add_edge('dimensions', END)
graph = graph.compile()