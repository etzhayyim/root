from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    purity: float
    gmp_certified: bool
    compliance_report: str

def validate_purity(state: ProcurementState):
    is_valid = state['purity'] >= 99.0
    return {'compliance_report': 'Passed' if is_valid else 'Failed: Purity check'}

def check_gmp(state: ProcurementState):
    report = state['compliance_report']
    if state['gmp_certified']:
        return {'compliance_report': report + '; GMP Verified'}
    return {'compliance_report': report + '; GMP Missing'}

graph = StateGraph(ProcurementState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_gmp', check_gmp)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_gmp')
graph.add_edge('check_gmp', END)
graph = graph.compile()