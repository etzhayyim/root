from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ReagentState(TypedDict):
    commodity_code: str
    quality_docs: List[str]
    compliance_checks: List[str]
    status: str

def validate_docs(state: ReagentState) -> ReagentState:
    state['quality_docs'].append('SDS_VERIFIED')
    return state

def check_compliance(state: ReagentState) -> ReagentState:
    state['compliance_checks'].append('COLD_CHAIN_OK')
    state['status'] = 'READY_FOR_PROCUREMENT'
    return state

graph = StateGraph(ReagentState)
graph.add_node('validate', validate_docs)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()