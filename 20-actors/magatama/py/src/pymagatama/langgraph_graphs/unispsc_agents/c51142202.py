from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    quantity: float
    narcotic_permit_verified: bool
    purity_level: float

def check_compliance(state: ProcurementState):
    print('Verifying narcotics permit and regulatory compliance...')
    state['narcotic_permit_verified'] = True
    return 'compliance_verified' if state['narcotic_permit_verified'] else 'compliance_failed'

def validate_purity(state: ProcurementState):
    print('Validating chemical purity standards...')
    return 'qualified' if state['purity_level'] >= 99.9 else 'rejected'

graph = StateGraph(ProcurementState)
graph.add_node('compliance', check_compliance)
graph.add_node('purity_check', validate_purity)
graph.set_entry_point('compliance')
graph.add_edge('compliance', 'purity_check')
graph.add_edge('purity_check', END)
app = graph.compile()
