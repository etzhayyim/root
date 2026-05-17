from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ForgingState(TypedDict):
    part_id: str
    material_certified: bool
    inspection_passed: bool
    log: List[str]

def validate_material(state: ForgingState) -> ForgingState:
    state['material_certified'] = True
    state['log'].append('Material certification verified.')
    return state

def perform_inspection(state: ForgingState) -> ForgingState:
    state['inspection_passed'] = True
    state['log'].append('Ultrasonic inspection passed.')
    return state

graph = StateGraph(ForgingState)
graph.add_node('validate', validate_material)
graph.add_node('inspect', perform_inspection)
graph.set_entry_point('validate')
graph.add_edge('validate', 'inspect')
graph.add_edge('inspect', END)
app = graph.compile()