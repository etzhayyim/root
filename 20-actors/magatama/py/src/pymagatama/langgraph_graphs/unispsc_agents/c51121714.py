from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    batch_id: str
    purity_level: float
    qc_passed: bool

def validate_purity(state: ProcurementState):
    state['qc_passed'] = state['purity_level'] >= 99.0
    return state

def check_compliance(state: ProcurementState):
    print(f'Checking regulatory compliance for batch: {state.get('batch_id')}')
    return {'qc_passed': state['qc_passed']}

graph = StateGraph(ProcurementState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('compliance_check', check_compliance)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'compliance_check')
graph.add_edge('compliance_check', END)
graph = graph.compile()
