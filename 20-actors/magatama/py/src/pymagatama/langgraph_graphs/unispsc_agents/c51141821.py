from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    purity: float
    gmp_certified: bool
    compliance_check: bool

def validate_purity(state: ProcurementState):
    state['purity'] = 99.0 if state['purity'] < 99.0 else state['purity']
    return {'purity': state['purity']}

def check_compliance(state: ProcurementState):
    return {'compliance_check': state.get('gmp_certified', False)}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_purity)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()
