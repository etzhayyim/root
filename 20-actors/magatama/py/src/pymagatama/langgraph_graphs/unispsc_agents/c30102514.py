from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class LeadSheetState(TypedDict):
    purity_level: float
    thickness: float
    safety_clearance: bool
    validation_errors: List[str]

def validate_lead_specs(state: LeadSheetState):
    errors = []
    if state['purity_level'] < 99.9:
        errors.append('Purity below industrial threshold')
    if state['thickness'] <= 0:
        errors.append('Invalid thickness specification')
    return {'validation_errors': errors}

def check_safety_protocols(state: LeadSheetState):
    status = state.get('safety_clearance', False)
    return {'safety_clearance': status}

workflow = StateGraph(LeadSheetState)
workflow.add_node('validate', validate_lead_specs)
workflow.add_node('safety', check_safety_protocols)
workflow.set_entry_point('validate')
workflow.add_edge('validate', 'safety')
workflow.add_edge('safety', END)
graph = workflow.compile()