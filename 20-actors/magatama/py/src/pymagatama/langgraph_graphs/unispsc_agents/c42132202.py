from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class FingerCotState(TypedDict):
    material: str
    size: str
    is_anti_static: bool
    compliance_docs: List[str]
    approved: bool

def validate_specs(state: FingerCotState):
    state['approved'] = 'ISO 13485' in state['compliance_docs'] and state['size'] in ['S', 'M', 'L']
    return state

def check_material(state: FingerCotState):
    if state['material'] not in ['latex', 'nitrile']:
        state['approved'] = False
    return state

graph = StateGraph(FingerCotState)
graph.add_node('validate', validate_specs)
graph.add_node('material_check', check_material)
graph.set_entry_point('validate')
graph.add_edge('validate', 'material_check')
graph.add_edge('material_check', END)
graph = graph.compile()
