from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    chemical_data: dict
    validation_issues: list
    status: str

def validate_drug_specs(state: ProcurementState):
    issues = []
    if state['chemical_data'].get('purity_pct', 0) < 99.0:
        issues.append('Purity below pharmaceutical threshold')
    return {'validation_issues': issues, 'status': 'validated' if not issues else 'rejected'}

def route_by_status(state: ProcurementState):
    return 'end' if state['status'] == 'validated' else 'end'

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_drug_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()