from typing import TypedDict, Annotated, List
import operator
from langgraph.graph import StateGraph, END

class WasherState(TypedDict):
    specs: dict
    validation_log: List[str]
    is_compliant: bool

def validate_material(state: WasherState):
    log = state.get('validation_log', [])
    material = state['specs'].get('material')
    if not material:
        log.append('Material missing')
    return {'validation_log': log}

def structural_check(state: WasherState):
    log = state.get('validation_log', [])
    if state['specs'].get('pressure_mpa', 0) < 0:
        log.append('Invalid pressure rating')
    return {'validation_log': log, 'is_compliant': len(log) == 0}

graph = StateGraph(WasherState)
graph.add_node('material_check', validate_material)
graph.add_node('structural_check', structural_check)
graph.set_entry_point('material_check')
graph.add_edge('material_check', 'structural_check')
graph.add_edge('structural_check', END)
graph = graph.compile()
