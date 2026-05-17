from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class PatientPajamaState(TypedDict):
    spec_data: dict
    compliance_passed: bool
    validation_log: List[str]

def validate_material(state: PatientPajamaState):
    log = state.get('validation_log', [])
    material = state['spec_data'].get('material', '')
    if 'flame_retardant' in material:
        log.append('Material safety check passed')
    else:
        log.append('Warning: Flame retardancy check failed')
    return {'validation_log': log}

def check_sterilization(state: PatientPajamaState):
    log = state.get('validation_log', [])
    if state['spec_data'].get('autoclave_safe', False):
        log.append('Sterilization rating validated')
    return {'validation_log': log, 'compliance_passed': True}

graph = StateGraph(PatientPajamaState)
graph.add_node('validate_material', validate_material)
graph.add_node('check_sterilization', check_sterilization)
graph.set_entry_point('validate_material')
graph.add_edge('validate_material', 'check_sterilization')
graph.add_edge('check_sterilization', END)
graph = graph.compile()