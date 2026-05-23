from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcessingState(TypedDict):
    component_id: str
    material_grade: str
    tolerance_check: bool
    is_compliant: bool

def validate_specs(state: ProcessingState):
    # Simulate geometric tolerance and material validation logic
    state['is_compliant'] = state['tolerance_check'] and state['material_grade'] in ['6061-T6', '2024-T3']
    return state

def run_compliance_check(state: ProcessingState):
    print(f'Validating component {state['component_id']}')
    return 'compliant' if state['is_compliant'] else 'non_compliant'

workflow = StateGraph(ProcessingState)
workflow.add_node('validate', validate_specs)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()
