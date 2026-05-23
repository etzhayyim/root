from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class DialysisClampsState(TypedDict):
    part_number: str
    quality_docs: List[str]
    is_sterile: bool
    compliance_validated: bool

def validate_quality_certs(state: DialysisClampsState):
    required = ['ISO_13485', 'CE_Mark', 'FDA_510k']
    valid = all(doc in state['quality_docs'] for doc in required)
    return {'compliance_validated': valid}

def process_clamp_procurement(state: DialysisClampsState):
    if state['is_sterile'] and state['compliance_validated']:
        return 'APPROVE'
    return 'REJECT'

graph = StateGraph(DialysisClampsState)
graph.add_node('validate', validate_quality_certs)
graph.add_node('process', process_clamp_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.compile()
