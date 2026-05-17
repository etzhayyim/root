from typing import TypedDict
from langgraph.graph import StateGraph, END

class MotorState(TypedDict):
    specs: dict
    validated: bool
    error: str

def validate_specs(state: MotorState):
    required = ['rated_voltage_V', 'shaft_diameter_mm']
    if all(k in state['specs'] for k in required):
        return {'validated': True}
    return {'validated': False, 'error': 'Missing required technical parameters'}

def check_export(state: MotorState):
    # Dual-use check logic
    return {'validated': True}

graph = StateGraph(MotorState)
graph.add_node('validate', validate_specs)
graph.add_node('export_check', check_export)
graph.add_edge('validate', 'export_check')
graph.add_edge('export_check', END)
graph.set_entry_point('validate')