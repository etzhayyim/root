from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    material_id: str
    purity: float
    regulatory_docs: List[str]
    status: str

def validate_compliance(state: ProcurementState):
    if state['purity'] >= 99.0 and 'GMP' in state.get('regulatory_docs', []):
        return {'status': 'APPROVED'}
    return {'status': 'REJECTED'}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
