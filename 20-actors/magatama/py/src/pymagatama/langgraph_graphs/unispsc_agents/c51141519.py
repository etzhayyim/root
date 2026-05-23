from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class MephenytoinState(TypedDict):
    batch_id: str
    purity_level: float
    compliance_docs: List[str]
    validation_status: bool

def validate_purity(state: MephenytoinState):
    state['validation_status'] = state['purity_level'] >= 99.0
    return state

def check_compliance(state: MephenytoinState):
    return {'validation_status': state['validation_status'] and len(state['compliance_docs']) >= 3}

graph = StateGraph(MephenytoinState)
graph.add_node('validate', validate_purity)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
app = graph.compile()
