from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class SurgicalTableState(TypedDict):
    table_id: str
    specs: dict
    validation_status: str
    approval_required: bool

def validate_specs(state: SurgicalTableState):
    required = ['Load Capacity', 'ISO 13485']
    valid = all(k in state['specs'] for k in required)
    return {'validation_status': 'PASS' if valid else 'FAIL', 'approval_required': not valid}

def route_by_validation(state: SurgicalTableState):
    return 'validate' if state['validation_status'] == 'FAIL' else 'end'

graph = StateGraph(SurgicalTableState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()
