from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class TretinoinState(TypedDict):
    batch_id: str
    compliance_docs: List[str]
    temp_log: float
    is_approved: bool

def validate_compliance(state: TretinoinState):
    state['is_approved'] = 'GMP_CERT' in state['compliance_docs'] and state['temp_log'] <= 25.0
    return state

graph = StateGraph(TretinoinState)
graph.add_node('validation', validate_compliance)
graph.set_entry_point('validation')
graph.add_edge('validation', END)
graph = graph.compile()