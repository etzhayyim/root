from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class VacuumMoldState(TypedDict):
    specs: dict
    validation_log: List[str]
    approved: bool

def validate_material(state: VacuumMoldState):
    log = state.get('validation_log', [])
    if 'material_grade' not in state['specs']:
        log.append('Error: Missing Material Grade')
    return {'validation_log': log}

def check_geometry(state: VacuumMoldState):
    log = state.get('validation_log', [])
    if state['specs'].get('thickness', 0) < 0.5:
        log.append('Warning: Thin wall section detected')
    return {'validation_log': log}

graph = StateGraph(VacuumMoldState)
graph.add_node('validate_material', validate_material)
graph.add_node('check_geometry', check_geometry)
graph.add_edge('validate_material', 'check_geometry')
graph.add_edge('check_geometry', END)
graph.set_entry_point('validate_material')
graph = graph.compile()
