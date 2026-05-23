from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class CatheterState(TypedDict):
    commodity_code: str
    spec_data: dict
    validation_passed: bool
    log: List[str]

def validate_sterility(state: CatheterState):
    cert = state['spec_data'].get('sterility_certificate_id')
    is_valid = cert is not None and len(cert) > 5
    return {'validation_passed': is_valid, 'log': ['Sterility validation performed']}

def approve_workflow(state: CatheterState):
    return {'log': ['Workflow approved for deployment']}

graph = StateGraph(CatheterState)
graph.add_node('validate', validate_sterility)
graph.add_node('approve', approve_workflow)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()
