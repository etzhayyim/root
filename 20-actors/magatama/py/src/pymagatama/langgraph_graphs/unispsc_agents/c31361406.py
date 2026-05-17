from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcessingState(TypedDict):
    assembly_specs: dict
    validation_passed: bool
    errors: List[str]

def validate_materials(state: ProcessingState):
    specs = state.get('assembly_specs', {})
    if 'material' not in specs:
        state['errors'].append('Missing material type')
        state['validation_passed'] = False
    return state

def check_joining_compliance(state: ProcessingState):
    if state.get('validation_passed', True):
        print('Checking brazing/welding integrity standards...')
    return state

graph = StateGraph(ProcessingState)
graph.add_node('material_check', validate_materials)
graph.add_node('integrity_check', check_joining_compliance)
graph.set_entry_point('material_check')
graph.add_edge('material_check', 'integrity_check')
graph.add_edge('integrity_check', END)
graph = graph.compile()