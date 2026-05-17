from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    purity: float
    has_coa: bool
    compliant: bool

def validate_purity(state: ProcurementState):
    if state['purity'] >= 99.0:
        return {'compliant': True}
    return {'compliant': False}

def check_compliance(state: ProcurementState):
    print('Verifying GMP certification and COA...')
    return {'compliant': state['has_coa']}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_purity)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()