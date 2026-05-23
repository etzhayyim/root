from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CatheterState(TypedDict):
    material: str
    is_sterile: bool
    compliance_docs: List[str]
    approved: bool

def validate_compliance(state: CatheterState):
    is_compliant = 'iso_13485' in state['compliance_docs'] and state['is_sterile']
    return {'approved': is_compliant}

def process_procurement(state: CatheterState):
    print(f'Processing catheter procurement: {state}')
    return {'approved': True}

graph = StateGraph(CatheterState)
graph.add_node('validate', validate_compliance)
graph.add_node('process', process_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph = graph.compile()
