from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ElectrotherapyState(TypedDict):
    product_id: str
    compliance_docs: List[str]
    validation_passed: bool

def validate_compliance(state: ElectrotherapyState):
    required = ['ISO13485', 'Biocompatibility_Test']
    passed = all(doc in state['compliance_docs'] for doc in required)
    return {'validation_passed': passed}

def route_by_validation(state: ElectrotherapyState):
    return 'process' if state['validation_passed'] else 'flag_error'

graph = StateGraph(ElectrotherapyState)
graph.add_node('validate', validate_compliance)
graph.add_node('process', lambda x: x)
graph.add_node('flag_error', lambda x: x)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_validation)
graph.add_edge('process', END)
graph.add_edge('flag_error', END)

app = graph.compile()