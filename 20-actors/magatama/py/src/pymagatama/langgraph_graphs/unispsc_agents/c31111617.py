from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class ZincState(TypedDict):
    spec_data: dict
    validation_passed: bool
    error_log: list

def validate_material_specs(state: ZincState):
    spec = state['spec_data']
    passed = 'material_grade' in spec and 'tolerance' in spec
    return {'validation_passed': passed}

def process_extrusion_workflow(state: ZincState):
    print('Executing precision analysis for impact extrusion...')
    return {'error_log': []}

graph = StateGraph(ZincState)
graph.add_node('validate', validate_material_specs)
graph.add_node('process', process_extrusion_workflow)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph = graph.compile()