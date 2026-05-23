from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class State(TypedDict):
    batch_id: str
    purity_level: float
    compliance_docs: List[str]
    approved: bool

def validate_purity(state: State) -> State:
    state['approved'] = state['purity_level'] >= 99.0
    return state

def check_compliance(state: State) -> State:
    if 'gmp_cert' not in state['compliance_docs']:
        state['approved'] = False
    return state

graph = StateGraph(State)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_compliance', check_compliance)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_compliance')
graph.add_edge('check_compliance', END)
graph = graph.compile()
