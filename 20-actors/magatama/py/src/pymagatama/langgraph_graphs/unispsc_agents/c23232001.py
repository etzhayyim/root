from typing import TypedDict
from langgraph.graph import StateGraph, END

class MetalMachineryState(TypedDict):
    spec_data: dict
    validation_results: list
    is_compliant: bool

def validate_safety_certs(state: MetalMachineryState):
    certs = state['spec_data'].get('safety_certs', [])
    is_valid = len(certs) > 0
    return {'validation_results': [f'Cert validation: {is_valid}'], 'is_compliant': is_valid}

def check_voltage(state: MetalMachineryState):
    voltage = state['spec_data'].get('voltage', 0)
    valid = 110 <= voltage <= 480
    return {'validation_results': state['validation_results'] + [f'Voltage {voltage} valid: {valid}']}

graph = StateGraph(MetalMachineryState)
graph.add_node('safety_check', validate_safety_certs)
graph.add_node('voltage_check', check_voltage)
graph.set_entry_point('safety_check')
graph.add_edge('safety_check', 'voltage_check')
graph.add_edge('voltage_check', END)
graph = graph.compile()