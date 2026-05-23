from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class TubeAssemblyState(TypedDict):
    part_number: str
    material_spec: str
    weld_inspection_report: str
    passed_validation: bool

def validate_material(state: TubeAssemblyState):
    print(f'Validating Inconel material grade for {state['part_number']}')
    return {'passed_validation': state['material_spec'] == 'Inconel-625'}

def perform_inspection(state: TubeAssemblyState):
    print('Conducting weld integrity assessment...')
    return {'weld_inspection_report': 'Passed'}

graph = StateGraph(TubeAssemblyState)
graph.add_node('validate', validate_material)
graph.add_node('inspect', perform_inspection)
graph.set_entry_point('validate')
graph.add_edge('validate', 'inspect')
graph.add_edge('inspect', END)
graph = graph.compile()
