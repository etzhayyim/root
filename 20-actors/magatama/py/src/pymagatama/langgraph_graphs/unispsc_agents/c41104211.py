from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SoftenerState(TypedDict):
    chemical_name: str
    purity: float
    has_sds: bool
    is_approved: bool

def validate_purity(state: SoftenerState):
    return {'is_approved': state['purity'] >= 99.0}

def check_sds(state: SoftenerState):
    return {'is_approved': state['has_sds']}

graph = StateGraph(SoftenerState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_sds', check_sds)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_sds')
graph.add_edge('check_sds', END)
app = graph.compile()