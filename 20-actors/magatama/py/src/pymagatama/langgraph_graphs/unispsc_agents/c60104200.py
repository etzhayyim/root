from typing import TypedDict
from langgraph.graph import StateGraph, END

class WaterTestingState(TypedDict):
    test_parameters: dict
    compliance_report: str
    validation_status: bool

def validate_sensor_specs(state: WaterTestingState):
    # Simulate validation logic for water testing hardware
    state['validation_status'] = all(param in state['test_parameters'] for param in ['ph', 'conductivity'])
    print('Validating hardware specifications...')
    return state

def generate_compliance_document(state: WaterTestingState):
    if state['validation_status']:
        state['compliance_report'] = 'Certified for Environmental Testing'
    return state

graph = StateGraph(WaterTestingState)
graph.add_node('validate', validate_sensor_specs)
graph.add_node('certify', generate_compliance_document)
graph.add_edge('validate', 'certify')
graph.add_edge('certify', END)
graph.set_entry_point('validate')
graph.set_entry_point('validate')
