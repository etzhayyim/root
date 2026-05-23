from langgraph.graph import StateGraph, END
from typing import TypedDict, List
class StentState(TypedDict):
    stent_id: str
    compliance_docs: List[str]
    validation_status: bool
def validate_compliance(state: StentState):
    state['validation_status'] = all(['ISO_CERT' in state['compliance_docs'], 'STERILIZATION_REPORT' in state['compliance_docs']])
    return state
graph = StateGraph(StentState)
graph.add_node('validate', validate_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
