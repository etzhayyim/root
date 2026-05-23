from typing import TypedDict
from langgraph.graph import StateGraph, END

class DisplayCaseState(TypedDict):
    specs: dict
    validation_passed: bool

def validate_thermal_specs(state: DisplayCaseState):
    temp = state['specs'].get('temp_range', 0)
    return {'validation_passed': temp > 0}

def check_compliance(state: DisplayCaseState):
    compliance = state['specs'].get('certification', [])
    return {'validation_passed': 'NSF' in compliance}

graph = StateGraph(DisplayCaseState)
graph.add_node('thermal_validation', validate_thermal_specs)
graph.add_node('compliance_check', check_compliance)
graph.add_edge('thermal_validation', 'compliance_check')
graph.add_edge('compliance_check', END)
graph.set_entry_point('thermal_validation')
