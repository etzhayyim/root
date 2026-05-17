from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ReagentState(TypedDict):
    commodity_code: str
    quality_docs: List[str]
    temp_log_verified: bool
    is_compliant: bool

def validate_quality(state: ReagentState):
    verified = len(state['quality_docs']) >= 2
    return {'is_compliant': verified}

def check_cold_chain(state: ReagentState):
    return {'temp_log_verified': True}

graph = StateGraph(ReagentState)
graph.add_node('validate', validate_quality)
graph.add_node('cold_chain', check_cold_chain)
graph.set_entry_point('validate')
graph.add_edge('validate', 'cold_chain')
graph.add_edge('cold_chain', END)
graph = graph.compile()