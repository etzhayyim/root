from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class RadiationProductState(TypedDict):
    product_id: str
    compliance_docs: List[str]
    validation_passed: bool

def check_compliance(state: RadiationProductState):
    required = ['ISO_13485', 'NRC_License']
    passed = all(doc in state['compliance_docs'] for doc in required)
    return {'validation_passed': passed}

def route_by_compliance(state: RadiationProductState):
    return 'validate' if not state['validation_passed'] else END

graph = StateGraph(RadiationProductState)
graph.add_node('validate', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
