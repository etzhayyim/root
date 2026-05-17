from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class BearingProcurementState(TypedDict):
    part_number: str
    quality_docs: List[str]
    verification_status: bool
    compliance_score: float

def validate_specs(state: BearingProcurementState):
    print(f'Validating specs for {state["part_number"]}')
    return {'verification_status': True, 'compliance_score': 0.95}

def check_compliance(state: BearingProcurementState):
    return 'compliant' if state['compliance_score'] > 0.9 else 'rejected'

graph = StateGraph(BearingProcurementState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()