from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class AuditState(TypedDict):
    specs: dict
    valid: bool
    errors: List[str]

def validate_specs(state: AuditState):
    errors = []
    if state['specs'].get('power', 0) <= 0:
        errors.append('Invalid output power')
    return {'valid': len(errors) == 0, 'errors': errors}

workflow = StateGraph(AuditState)
workflow.add_node('validation', validate_specs)
workflow.set_entry_point('validation')
workflow.add_edge('validation', END)
graph = workflow.compile()
