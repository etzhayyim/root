from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ChemicalState(TypedDict):
    purity: float
    cas_number: str
    compliance_docs: List[str]
    status: str

def validate_coa(state: ChemicalState):
    if state['purity'] >= 99.0:
        return {'status': 'validated'}
    return {'status': 'rejected'}

def check_sds(state: ChemicalState):
    if 'SDS_available' in state['compliance_docs']:
        return {'status': 'ready'}
    return {'status': 'missing_docs'}

graph = StateGraph(ChemicalState)
graph.add_node('validate_coa', validate_coa)
graph.add_node('check_sds', check_sds)
graph.set_entry_point('validate_coa')
graph.add_edge('validate_coa', 'check_sds')
graph.add_edge('check_sds', END)
graph = graph.compile()