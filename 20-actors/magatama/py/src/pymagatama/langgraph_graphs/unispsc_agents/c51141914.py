from typing import TypedDict
from langgraph.graph import StateGraph, END
class ClorazepateState(TypedDict):
    purity: float
    compliant: bool
    gmp_status: str

def validate_purity(state: ClorazepateState):
    state['compliant'] = state['purity'] >= 99.0
    return state

def check_gmp(state: ClorazepateState):
    state['compliant'] = state['compliant'] and (state['gmp_status'] == 'certified')
    return state

graph = StateGraph(ClorazepateState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_gmp', check_gmp)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_gmp')
graph.add_edge('check_gmp', END)
app = graph.compile()