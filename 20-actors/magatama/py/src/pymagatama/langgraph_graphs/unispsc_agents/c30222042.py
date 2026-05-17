from typing import TypedDict
from langgraph.graph import StateGraph, END

class HighwayState(TypedDict):
    project_id: str
    infrastructure_status: str
    compliance_validated: bool

def validate_infrastructure(state: HighwayState):
    print(f'Validating infrastructure for project: {state['project_id']}')
    return {'compliance_validated': True, 'infrastructure_status': 'Validated'}

def approve_project(state: HighwayState):
    return {'infrastructure_status': 'Approved'}

graph = StateGraph(HighwayState)
graph.add_node('validate', validate_infrastructure)
graph.add_node('approve', approve_project)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()