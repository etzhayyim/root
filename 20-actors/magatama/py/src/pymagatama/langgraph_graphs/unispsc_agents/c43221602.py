from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class DSLWorkflowState(TypedDict):
    shelf_id: str
    compliance_verified: bool
    thermal_test_passed: bool

def validate_specs(state: DSLWorkflowState):
    print(f'Validating specs for shelf: {state[\'shelf_id\']}')
    return {'compliance_verified': True}

def perform_thermal_test(state: DSLWorkflowState):
    print('Running thermal stress test.')
    return {'thermal_test_passed': True}

graph = StateGraph(DSLWorkflowState)
graph.add_node('validate', validate_specs)
graph.add_node('thermal_test', perform_thermal_test)
graph.add_edge('validate', 'thermal_test')
graph.add_edge('thermal_test', END)
graph.set_entry_point('validate')
app = graph.compile()