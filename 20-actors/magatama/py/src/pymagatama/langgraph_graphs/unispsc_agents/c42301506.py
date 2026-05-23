from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class AuditState(TypedDict):
    item_name: str
    compliance_docs: List[str]
    status: str

def validate_specs(state: AuditState):
    if all(doc in state['compliance_docs'] for doc in ['FDA_ISO_Cert', 'Acoustic_Test_Report']):
        return {'status': 'CERTIFIED'}
    return {'status': 'PENDING_REVIEW'}

graph = StateGraph(AuditState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
