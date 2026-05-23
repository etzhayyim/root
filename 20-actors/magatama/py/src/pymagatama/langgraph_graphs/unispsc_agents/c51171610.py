from typing import TypedDict
from langgraph.graph import StateGraph, END

class SennaState(TypedDict):
    batch_id: str
    purity_level: float
    compliance_docs: bool
    approved: bool

def validate_quality(state: SennaState):
    is_pure = state['purity_level'] >= 98.0
    return {'approved': is_pure and state['compliance_docs']}

graph = StateGraph(SennaState)
graph.add_node('quality_check', validate_quality)
graph.set_entry_point('quality_check')
graph.add_edge('quality_check', END)
graph = graph.compile()
