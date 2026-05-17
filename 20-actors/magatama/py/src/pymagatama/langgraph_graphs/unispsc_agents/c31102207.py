from typing import TypedDict
from langgraph.graph import StateGraph, END

class CastingState(TypedDict):
    part_id: str
    material_spec: dict
    inspection_result: str

def validate_material(state: CastingState):
    print(f'Validating material specifications for {state['part_id']}')
    return {'inspection_result': 'verified' if 'ASTM' in state['material_spec'] else 'failed'}

def conduct_cad_check(state: CastingState):
    print('Performing dimensional tolerance analysis...')
    return {'inspection_result': 'passed'}

graph = StateGraph(CastingState)
graph.add_node('validate', validate_material)
graph.add_node('cad_check', conduct_cad_check)
graph.add_edge('validate', 'cad_check')
graph.add_edge('cad_check', END)
graph.set_entry_point('validate')
process = graph.compile()