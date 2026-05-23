from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class RisperidoneState(TypedDict):
    batch_id: str
    purity: float
    storage_temp: float
    compliance_docs: List[str]
    approved: bool

def validate_purity(state: RisperidoneState):
    state['approved'] = state['purity'] >= 99.0
    return state

def validate_storage(state: RisperidoneState):
    if not (2 <= state['storage_temp'] <= 8):
        state['approved'] = False
    return state

graph = StateGraph(RisperidoneState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('validate_storage', validate_storage)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'validate_storage')
graph.add_edge('validate_storage', END)
app = graph.compile()
