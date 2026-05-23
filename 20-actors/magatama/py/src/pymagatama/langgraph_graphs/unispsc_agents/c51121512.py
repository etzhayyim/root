from langgraph.graph import StateGraph, END
from typing import TypedDict

class ProcurementState(TypedDict):
    api_purity: float
    gmp_certified: bool
    compliance_check: bool

def validate_api_spec(state: ProcurementState):
    if state['api_purity'] >= 99.0 and state['gmp_certified']:
        return {'compliance_check': True}
    return {'compliance_check': False}

def finalize_procurement(state: ProcurementState):
    print('Procurement validated for Pharmaceutical supply.')
    return {}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_api_spec)
graph.add_node('finalize', finalize_procurement)
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph.set_entry_point('validate')
graph = graph.compile()
