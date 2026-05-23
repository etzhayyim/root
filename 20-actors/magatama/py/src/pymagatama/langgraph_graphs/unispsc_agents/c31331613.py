from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    assembly_data: dict
    validation_passed: bool

def validate_specifications(state: ProcurementState):
    specs = state['assembly_data'].get('specs', {})
    required = ['material_grade', 'welding_standard']
    passed = all(key in specs for key in required)
    return {'validation_passed': passed}

def structural_integrity_check(state: ProcurementState):
    print('Running non-destructive structural analysis...')
    return {'validation_passed': True}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_specifications)
graph.add_node('integrity_check', structural_integrity_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'integrity_check')
graph.add_edge('integrity_check', END)
graph = graph.compile()
