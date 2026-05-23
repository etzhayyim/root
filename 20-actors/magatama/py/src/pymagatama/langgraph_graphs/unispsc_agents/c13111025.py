from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
import operator

class PhosphateState(TypedDict):
    purity: float
    safety_check: bool
    batch_id: str
    processing_logs: Annotated[list[str], operator.add]

def validate_purity(state: PhosphateState) -> PhosphateState:
    if state['purity'] >= 99.5:
        return {'processing_logs': ['Purity validation passed']}
    return {'processing_logs': ['Purity validation failed']}

def conduct_safety_audit(state: PhosphateState) -> PhosphateState:
    return {'safety_check': True, 'processing_logs': ['Safety audit completed']}

graph = StateGraph(PhosphateState)
graph.add_node('validate', validate_purity)
graph.add_node('audit', conduct_safety_audit)
graph.set_entry_point('validate')
graph.add_edge('validate', 'audit')
graph.add_edge('audit', END)

app = graph.compile()
