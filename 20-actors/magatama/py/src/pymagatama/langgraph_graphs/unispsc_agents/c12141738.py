from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class CatalystState(TypedDict):
    purity: float
    batch_id: str
    quality_checks: List[str]
    approved: bool

def validate_purity(state: CatalystState) -> CatalystState:
    if state.get('purity', 0) >= 99.99:
        state['quality_checks'].append('Purity Verified')
    return state

def check_compliance(state: CatalystState) -> CatalystState:
    state['approved'] = 'Purity Verified' in state['quality_checks']
    return state

builder = StateGraph(CatalystState)
builder.add_node('validate', validate_purity)
builder.add_node('compliance', check_compliance)
builder.add_edge('validate', 'compliance')
builder.add_edge('compliance', END)
builder.set_entry_point('validate')
graph = builder.compile()
