from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class HandkerchiefState(TypedDict):
    specs: dict
    approved: bool

def validate_materials(state: HandkerchiefState):
    material = state['specs'].get('material', '')
    return {'approved': material in ['cotton', 'linen', 'polyester']}

def check_dimensions(state: HandkerchiefState):
    dim = state['specs'].get('dimensions', (0, 0))
    return {'approved': state['approved'] and (dim[0] > 10 and dim[1] > 10)}

graph = StateGraph(HandkerchiefState)
graph.add_node('validate_materials', validate_materials)
graph.add_node('check_dimensions', check_dimensions)
graph.set_entry_point('validate_materials')
graph.add_edge('validate_materials', 'check_dimensions')
graph.add_edge('check_dimensions', END)
graph = graph.compile()
