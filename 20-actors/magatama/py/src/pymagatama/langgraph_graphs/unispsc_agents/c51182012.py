from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PrasteroneState(TypedDict):
    purity: float
    compliance_docs: List[str]
    status: str

def validate_quality(state: PrasteroneState):
    if state['purity'] >= 99.0:
        return {'status': 'quality_verified'}
    return {'status': 'quality_rejected'}

def check_compliance(state: PrasteroneState):
    if 'COA' in state['compliance_docs']:
        return {'status': 'compliance_verified'}
    return {'status': 'compliance_failed'}

graph_builder = StateGraph(PrasteroneState)
graph_builder.add_node('validate', validate_quality)
graph_builder.add_node('compliance', check_compliance)
graph_builder.set_entry_point('validate')
graph_builder.add_edge('validate', 'compliance')
graph_builder.add_edge('compliance', END)
graph = graph_builder.compile()