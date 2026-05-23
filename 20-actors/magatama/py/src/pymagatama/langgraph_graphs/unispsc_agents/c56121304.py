from typing import TypedDict
from langgraph.graph import StateGraph, END

class PlanningTableState(TypedDict):
    dimensions: dict
    material_certified: bool
    approved: bool

def validate_dimensions(state: PlanningTableState):
    width = state['dimensions'].get('width', 0)
    state['approved'] = width > 1200
    return state

def check_materials(state: PlanningTableState):
    state['material_certified'] = True
    return state

graph = StateGraph(PlanningTableState)
graph.add_node('validate', validate_dimensions)
graph.add_node('certify', check_materials)
graph.set_entry_point('validate')
graph.add_edge('validate', 'certify')
graph.add_edge('certify', END)
graph = graph.compile()
