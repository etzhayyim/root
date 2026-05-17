from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class FastenerState(TypedDict):
    part_id: str
    material_grade: str
    spec_compliance: bool
    inspection_result: str

def validate_material(state: FastenerState) -> FastenerState:
    # Logic to verify material grade against industry standards
    state['spec_compliance'] = state['material_grade'] in ['Grade 8.8', 'Grade 10.9']
    return state

def run_inspection(state: FastenerState) -> FastenerState:
    # Logic for mechanical inspection simulation
    if state['spec_compliance']:
        state['inspection_result'] = 'PASSED_MECHANICAL_TEST'
    else:
        state['inspection_result'] = 'FAILED_MATERIAL_GRADE'
    return state

graph = StateGraph(FastenerState)
graph.add_node('validate', validate_material)
graph.add_node('inspect', run_inspection)
graph.add_edge('validate', 'inspect')
graph.add_edge('inspect', END)
graph.set_entry_point('validate')
graph = graph.compile()