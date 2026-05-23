from typing import TypedDict
from langgraph.graph import StateGraph, END

class DieProcurementState(TypedDict):
    spec_data: dict
    validation_passed: bool

def validate_die_specs(state: DieProcurementState):
    specs = state['spec_data']
    passed = all(key in specs for key in ['blade_height', 'steel_grade'])
    print(f'Validating die specs: {passed}')
    return {'validation_passed': passed}

def route_by_validation(state: DieProcurementState):
    return 'process' if state['validation_passed'] else END

workflow = StateGraph(DieProcurementState)
workflow.add_node('process', validate_die_specs)
workflow.set_entry_point('process')
workflow.add_edge('process', END)
graph = workflow.compile()
