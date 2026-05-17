from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class AuditState(TypedDict):
    items: List[str]
    approved: bool
    compliance_score: float

def validate_materials(state: AuditState):
    # Simulate material compliance check
    state['approved'] = all('cert' in item.lower() for item in state['items'])
    state['compliance_score'] = 1.0 if state['approved'] else 0.0
    return state

graph = StateGraph(AuditState)
graph.add_node('validate', validate_materials)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()