from typing import TypedDict
from langgraph.graph import StateGraph, END

class EquipmentState(TypedDict):
    spec_data: dict
    validation_results: list
    is_compliant: bool

def validate_optics(state: EquipmentState):
    specs = state['spec_data']
    results = []
    if 'wavelength' not in specs: results.append('Missing wavelength')
    return {'validation_results': results, 'is_compliant': len(results) == 0}

def export_control_check(state: EquipmentState):
    is_controlled = state['spec_data'].get('high_precision', False)
    return {'is_compliant': state['is_compliant'] and not is_controlled}

graph = StateGraph(EquipmentState)
graph.add_node('validate', validate_optics)
graph.add_node('export_check', export_control_check)
graph.add_edge('validate', 'export_check')
graph.add_edge('export_check', END)
graph.set_entry_point('validate')
graph = graph.compile()
