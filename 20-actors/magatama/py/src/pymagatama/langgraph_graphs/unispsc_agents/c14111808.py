from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class IndexCardState(TypedDict):
    content: str
    category: str
    is_verified: bool
    validation_log: List[str]

def classify_card(state: IndexCardState) -> IndexCardState:
    state['validation_log'].append('Classifying index card content.')
    state['category'] = 'Standard Filing' if len(state['content']) < 500 else 'Extended Data'
    return state

def verify_quality(state: IndexCardState) -> IndexCardState:
    state['is_verified'] = True
    state['validation_log'].append('Quality check passed for standard office stationery.')
    return state

graph = StateGraph(IndexCardState)
graph.add_node('classify', classify_card)
graph.add_node('verify', verify_quality)
graph.set_entry_point('classify')
graph.add_edge('classify', 'verify')
graph.add_edge('verify', END)
graph = graph.compile()