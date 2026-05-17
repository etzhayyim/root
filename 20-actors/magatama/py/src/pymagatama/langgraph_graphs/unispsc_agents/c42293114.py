from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class State(TypedDict):
    product_id: str
    compliance_docs: List[str]
    is_approved: bool

def validate_compliance(state: State):
    required = ['iso_13485', 'fda_clearance']
    approved = all(doc in state['compliance_docs'] for doc in required)
    return {'is_approved': approved}

def finalize_procurement(state: State):
    if state['is_approved']:
        print('Proceeding to quality inspection.')
    return {'is_approved': state['is_approved']}

graph = StateGraph(State)
graph.add_node('validate', validate_compliance)
graph.add_node('finalize', finalize_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()