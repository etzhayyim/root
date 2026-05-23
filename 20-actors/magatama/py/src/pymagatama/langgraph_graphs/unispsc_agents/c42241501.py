from typing import TypedDict
from langgraph.graph import StateGraph, END

class CastFootwearState(TypedDict):
    product_id: str
    compliance_docs: list
    is_approved: bool

def validate_compliance(state: CastFootwearState):
    state['is_approved'] = all(doc in state['compliance_docs'] for doc in ['ISO13485', 'CE_Medical_Mark'])
    print(f'Compliance status: {state['is_approved']}')
    return state

def route_step(state: CastFootwearState):
    return 'compliance_check'

graph = StateGraph(CastFootwearState)
graph.add_node('compliance_check', validate_compliance)
graph.set_entry_point('compliance_check')
graph.add_edge('compliance_check', END)
graph = graph.compile()
