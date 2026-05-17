from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class AluminumState(TypedDict):
    purity: float
    trace_metals: dict
    approved: bool
    logs: Annotated[Sequence[str], operator.add]

def validate_purity(state: AluminumState) -> AluminumState:
    is_valid = state['purity'] >= 99.9
    return {'approved': is_valid, 'logs': ['Purity check completed']}

def check_trace_metals(state: AluminumState) -> AluminumState:
    metals = state.get('trace_metals', {})
    risk = any(val > 0.01 for val in metals.values())
    return {'approved': not risk and state['approved'], 'logs': ['Metal analysis completed']}

graph = StateGraph(AluminumState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_trace_metals', check_trace_metals)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_trace_metals')
graph.add_edge('check_trace_metals', END)
app = graph.compile()