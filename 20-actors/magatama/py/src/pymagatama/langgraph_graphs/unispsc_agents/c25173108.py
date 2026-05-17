from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class NavSystemState(TypedDict):
    part_number: str
    spec_sheet: dict
    validation_checks: List[str]
    approved: bool

def validate_specs(state: NavSystemState):
    checks = []
    if state['spec_sheet'].get('automotive_grade'):
        checks.append('Compliance Verified: AEC-Q100')
    else:
        checks.append('Error: Non-automotive grade component')
    return {'validation_checks': checks, 'approved': len(checks) == 1}

workflow = StateGraph(NavSystemState)
workflow.add_node('validation', validate_specs)
workflow.set_entry_point('validation')
workflow.add_edge('validation', END)
graph = workflow.compile()