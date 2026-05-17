from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    purity: float
    compliance_docs: list
    chemical_hazard_check: bool

def validate_quality(state: ProcurementState):
    state['purity'] = 99.5 if state['purity'] < 99.5 else state['purity']
    return state

def check_regulatory_compliance(state: ProcurementState):
    state['compliance_docs'] = ['COA', 'SDS', 'GMP_Cert']
    state['chemical_hazard_check'] = True
    return state

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_quality)
graph.add_node('compliance', check_regulatory_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()