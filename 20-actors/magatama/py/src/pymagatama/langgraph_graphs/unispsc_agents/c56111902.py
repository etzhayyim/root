from typing import TypedDict
from langgraph.graph import StateGraph, END

class WorkSurfaceState(TypedDict):
    load_requirement: float
    material_spec: str
    is_validated: bool

def validate_load(state: WorkSurfaceState):
    state['is_validated'] = state['load_requirement'] > 0
    return state

def check_compliance(state: WorkSurfaceState):
    print(f'Checking compliance for material: {state['material_spec']}')
    return state

graph = StateGraph(WorkSurfaceState)
graph.add_node('validate_load', validate_load)
graph.add_node('check_compliance', check_compliance)
graph.set_entry_point('validate_load')
graph.add_edge('validate_load', 'check_compliance')
graph.add_edge('check_compliance', END)
graph = graph.compile()