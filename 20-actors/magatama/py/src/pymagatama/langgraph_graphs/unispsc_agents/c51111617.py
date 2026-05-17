from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    material_name: str
    quality_docs: List[str]
    requires_cold_chain: bool
    approved: bool

def validate_gmp(state: ProcurementState):
    state['approved'] = 'GMP_Certification' in state['quality_docs']
    return state

def check_compliance(state: ProcurementState):
    if state['approved'] and state['requires_cold_chain']:
        print('Routing to specialized pharmaceutical logistics.')
    return state

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_gmp)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()