from typing import TypedDict
from langgraph.graph import StateGraph, END

class AssemblyState(TypedDict):
    specs: dict
    validated: bool
    error_log: list

def validate_materials(state: AssemblyState):
    grade = state['specs'].get('material_grade')
    is_valid = grade in ['ASTM A514', 'ASTM A572']
    return {'validated': is_valid, 'error_log': [] if is_valid else ['Invalid material grade']}

def structural_check(state: AssemblyState):
    if state['validated']:
        print('Checking weld integrity...')
    return state

graph = StateGraph(AssemblyState)
graph.add_node('val', validate_materials)
graph.add_node('struct', structural_check)
graph.add_edge('val', 'struct')
graph.add_edge('struct', END)
graph.set_entry_point('val')
graph = graph.compile()