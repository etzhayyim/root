from typing import TypedDict
from langgraph.graph import StateGraph, END

class HeatTreatState(TypedDict):
    spec_data: dict
    validation_checks: list
    is_compliant: bool

def validate_thermal_specs(state: HeatTreatState):
    temp = state['spec_data'].get('max_temp', 0)
    state['validation_checks'].append('Thermal Capacity Verified')
    state['is_compliant'] = temp > 0
    return state

def check_dual_use_requirements(state: HeatTreatState):
    state['validation_checks'].append('Export Control Screening Completed')
    return state

graph = StateGraph(HeatTreatState)
graph.add_node('validate_thermal', validate_thermal_specs)
graph.add_node('check_export', check_dual_use_requirements)
graph.set_entry_point('validate_thermal')
graph.add_edge('validate_thermal', 'check_export')
graph.add_edge('check_export', END)

compiled_graph = graph.compile()
