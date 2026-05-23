from typing import TypedDict
from langgraph.graph import StateGraph, END

class HeatingEquipmentState(TypedDict):
    spec_data: dict
    is_compliant: bool

def validate_thermal_specs(state: HeatingEquipmentState):
    # Simulate thermal capacity and safety validation logic
    temp = state['spec_data'].get('temperature_range_celsius', 0)
    state['is_compliant'] = temp > 0 and temp < 2000
    return state

def check_dual_use(state: HeatingEquipmentState):
    # Logic to flag high-temp equipment for export control
    if state['spec_data'].get('temperature_range_celsius', 0) > 1500:
        print('Regulatory flag: Dual-use criteria met.')
    return state

graph = StateGraph(HeatingEquipmentState)
graph.add_node('validate', validate_thermal_specs)
graph.add_node('compliance_check', check_dual_use)
graph.add_edge('validate', 'compliance_check')
graph.add_edge('compliance_check', END)
graph.set_entry_point('validate')
graph = graph.compile()
