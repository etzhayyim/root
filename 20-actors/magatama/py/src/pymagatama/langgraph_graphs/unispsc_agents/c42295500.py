from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ImplantState(TypedDict):
    product_id: str
    compliance_docs: List[str]
    is_sterile: bool
    approved: bool

def validate_compliance(state: ImplantState):
    state['approved'] = 'ISO_13485' in state['compliance_docs'] and state['is_sterile']
    return state

def check_biocompatibility(state: ImplantState):
    print(f'Checking biocompatibility for {state['product_id']}')
    return state

graph = StateGraph(ImplantState)
graph.add_node('compliance', validate_compliance)
graph.add_node('safety', check_biocompatibility)
graph.set_entry_point('compliance')
graph.add_edge('compliance', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()