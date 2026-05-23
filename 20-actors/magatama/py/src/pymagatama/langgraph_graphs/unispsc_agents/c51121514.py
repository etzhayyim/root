from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    drug_name: str
    purity_level: float
    compliance_status: bool

def validate_drug_compliance(state: ProcurementState):
    state['compliance_status'] = state['purity_level'] >= 99.9
    return state

def check_gmp(state: ProcurementState):
    print(f'Verifying GMP certification for {state['drug_name']}')
    return state

workflow = StateGraph(ProcurementState)
workflow.add_node('validate', validate_drug_compliance)
workflow.add_node('gmp_check', check_gmp)
workflow.set_entry_point('gmp_check')
workflow.add_edge('gmp_check', 'validate')
workflow.add_edge('validate', END)
graph = workflow.compile()
