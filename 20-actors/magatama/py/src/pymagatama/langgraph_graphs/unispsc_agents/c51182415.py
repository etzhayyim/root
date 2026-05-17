from typing import TypedDict
from langgraph.graph import StateGraph, END

class ZoledronicState(TypedDict):
    purity: float
    compliance_docs: list
    temp_log: float

def validate_purity(state: ZoledronicState):
    assert state['purity'] >= 99.0, 'Purity below requirement'
    return {'status': 'purity_validated'}

def check_compliance(state: ZoledronicState):
    if len(state['compliance_docs']) < 2:
        raise ValueError('Insufficient regulatory documentation')
    return {'status': 'compliant'}

graph = StateGraph(ZoledronicState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_compliance', check_compliance)
graph.add_edge('validate_purity', 'check_compliance')
graph.add_edge('check_compliance', END)
graph.set_entry_point('validate_purity')
graph = graph.compile()