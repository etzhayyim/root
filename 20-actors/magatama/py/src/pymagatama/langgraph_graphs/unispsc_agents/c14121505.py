from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class FolderState(TypedDict):
    item_id: str
    material: str
    thickness: float
    is_compliant: bool
    validation_log: List[str]

def validate_material(state: FolderState):
    log = state.get('validation_log', [])
    if state['material'] in ['paper', 'plastic']:
        log.append(f'Material {state["material"]} is valid.')
        return {'is_compliant': True, 'validation_log': log}
    return {'is_compliant': False, 'validation_log': log + ['Invalid material type.']}

def check_dimensions(state: FolderState):
    log = state.get('validation_log', [])
    if state['thickness'] > 0.1:
        log.append('Thickness meets standard.')
        return {'validation_log': log}
    return {'is_compliant': False, 'validation_log': log + ['Insufficient thickness.']}

graph = StateGraph(FolderState)
graph.add_node('validate_material', validate_material)
graph.add_node('check_dimensions', check_dimensions)
graph.set_entry_point('validate_material')
graph.add_edge('validate_material', 'check_dimensions')
graph.add_edge('check_dimensions', END)
graph = graph.compile()