from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ProcurementState(TypedDict):
    material_name: str
    quality_docs: List[str]
    compliance_check: bool

def validate_api_specs(state: ProcurementState):
    required = {'coa', 'sds', 'gmp_cert'}
    state['compliance_check'] = required.issubset(set(state['quality_docs']))
    return state

graph = StateGraph(ProcurementState)
graph.add_node('validation', validate_api_specs)
graph.set_entry_point('validation')
graph.add_edge('validation', END)
graph = graph.compile()