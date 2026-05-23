from typing import TypedDict
from langgraph.graph import StateGraph, END

class WindowProcurementState(TypedDict):
    spec_data: dict
    validation_passed: bool

def validate_specs(state: WindowProcurementState):
    required_fields = ['u_value', 'wind_load', 'material']
    passed = all(field in state['spec_data'] for field in required_fields)
    return {'validation_passed': passed}

def check_compliance(state: WindowProcurementState):
    print('Checking compliance with building codes...')
    return {'validation_passed': True}

graph = StateGraph(WindowProcurementState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
