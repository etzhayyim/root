from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class AuditState(TypedDict):
    item_id: str
    compliance_docs: List[str]
    approved: bool

def validate_compliance(state: AuditState):
    required = ['ISO13485', 'Biocompatibility_Report']
    state['approved'] = all(doc in state['compliance_docs'] for doc in required)
    return state

graph = StateGraph(AuditState)
graph.add_node('validate', validate_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
app = graph.compile()