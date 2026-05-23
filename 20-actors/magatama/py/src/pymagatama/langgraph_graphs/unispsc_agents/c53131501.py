from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class MouthwashState(TypedDict):
    product_name: str
    compliance_docs: List[str]
    approved: bool

def validate_compliance(state: MouthwashState):
    required = ['FDA_Clearance', 'Microbial_Safety_Cert']
    all_present = all(doc in state['compliance_docs'] for doc in required)
    return {'approved': all_present}

graph = StateGraph(MouthwashState)
graph.add_node('validate', validate_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
