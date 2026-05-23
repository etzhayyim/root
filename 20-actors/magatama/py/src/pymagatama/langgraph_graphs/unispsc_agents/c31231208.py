from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcessingState(TypedDict):
    material_spec: dict
    validation_passed: bool
    export_license_required: bool

def validate_alloy_grade(state: ProcessingState):
    # Business logic for aerospace-grade magnesium validation
    state['validation_passed'] = state['material_spec'].get('grade') in ['AZ31B', 'ZK60A']
    return state

def check_export_compliance(state: ProcessingState):
    # Simplified dual-use check for magnesium exports
    state['export_license_required'] = state['material_spec'].get('purity', 0) > 99.9
    return state

graph = StateGraph(ProcessingState)
graph.add_node('validate', validate_alloy_grade)
graph.add_node('export_check', check_export_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export_check')
graph.add_edge('export_check', END)
graph = graph.compile()
