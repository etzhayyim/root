from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class AssemblyState(TypedDict):
    specs: dict
    validation_passed: bool
    errors: List[str]

def validate_materials(state: AssemblyState):
    grade = state['specs'].get('material_grade')
    if not grade or '304' not in grade and '316' not in grade:
        return {'validation_passed': False, 'errors': ['Invalid material grade']}
    return {'validation_passed': True}

def check_welding_certs(state: AssemblyState):
    if 'welding_standard' not in state['specs']:
        return {'validation_passed': False, 'errors': ['Missing welding certification']}
    return {'validation_passed': True}

graph = StateGraph(AssemblyState)
graph.add_node('material_check', validate_materials)
graph.add_node('weld_check', check_welding_certs)
graph.set_entry_point('material_check')
graph.add_edge('material_check', 'weld_check')
graph.add_edge('weld_check', END)
graph = graph.compile()
