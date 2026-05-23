from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CRMState(TypedDict):
    requirements: List[str]
    compliance_score: float
    api_endpoints: List[str]

def validate_requirements(state: CRMState):
    return {'compliance_score': 1.0 if len(state['requirements']) > 0 else 0.0}

def check_integration(state: CRMState):
    return {'api_endpoints': ['REST', 'GraphQL']}

graph = StateGraph(CRMState)
graph.add_node('validate', validate_requirements)
graph.add_node('integration', check_integration)
graph.set_entry_point('validate')
graph.add_edge('validate', 'integration')
graph.add_edge('integration', END)
graph = graph.compile()
