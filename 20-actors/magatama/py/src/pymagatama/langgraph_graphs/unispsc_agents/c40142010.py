from typing import TypedDict
from langgraph.graph import StateGraph, END

class HoseProcurementState(TypedDict):
    spec_data: dict
    compliance_status: bool
    validation_log: list

def validate_material(state: HoseProcurementState):
    material = state['spec_data'].get('lining_material_type', '')
    if material not in ['PTFE', 'PFA', 'FEP', 'ETFE']:
        return {'compliance_status': False, 'validation_log': ['Invalid lining material']}
    return {'compliance_status': True}

def check_pressure_rating(state: HoseProcurementState):
    rating = state['spec_data'].get('pressure_resistance_bar', 0)
    if rating < 10:
        return {'compliance_status': False, 'validation_log': ['Pressure rating too low']}
    return {'compliance_status': True}

graph = StateGraph(HoseProcurementState)
graph.add_node('material_check', validate_material)
graph.add_node('pressure_check', check_pressure_rating)
graph.add_edge('material_check', 'pressure_check')
graph.add_edge('pressure_check', END)
graph.set_entry_point('material_check')
