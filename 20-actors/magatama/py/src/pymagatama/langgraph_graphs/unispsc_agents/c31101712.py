from typing import TypedDict
from langgraph.graph import StateGraph, END

class CastingState(TypedDict):
    part_id: str
    material_spec: str
    inspection_passed: bool

def validate_material(state: CastingState):
    print(f'Validating bronze composition for {state['part_id']}')
    return {'inspection_passed': True}

def perform_dimensional_check(state: CastingState):
    print(f'Checking tolerances for {state['part_id']}')
    return {'inspection_passed': True}

graph = StateGraph(CastingState)
graph.add_node('validate', validate_material)
graph.add_node('cmi', perform_dimensional_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'cmi')
graph.add_edge('cmi', END)
graph = graph.compile()