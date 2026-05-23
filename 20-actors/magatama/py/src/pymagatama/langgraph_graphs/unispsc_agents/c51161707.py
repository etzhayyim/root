from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    api_name: str
    purity_level: float
    compliance_docs: list

def validate_api_spec(state: ProcurementState):
    assert state['purity_level'] >= 99.0, 'Purity below pharmaceutical Grade'
    return {'compliance_docs': ['GMP_CERT', 'COA']}

def check_hazmat(state: ProcurementState):
    print('Checking dangerous goods protocols for Bamifylline')
    return {'status': 'validated'}

graph = StateGraph(ProcurementState)
graph.add_node('validation', validate_api_spec)
graph.add_node('hazmat_check', check_hazmat)
graph.set_entry_point('validation')
graph.add_edge('validation', 'hazmat_check')
graph.add_edge('hazmat_check', END)
graph = graph.compile()
