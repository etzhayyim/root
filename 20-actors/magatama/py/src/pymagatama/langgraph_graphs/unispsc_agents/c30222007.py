from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class DepotState(TypedDict):
    facility_id: str
    compliance_docs: List[str]
    status: str

def validate_infrastructure(state: DepotState):
    if len(state['compliance_docs']) < 3:
        return {'status': 'INCOMPLETE_DOCS'}
    return {'status': 'VALIDATED'}

def deploy_depot_system(state: DepotState):
    print(f'Deploying depot logic for {state['facility_id']}')
    return {'status': 'DEPLOYED'}

graph = StateGraph(DepotState)
graph.add_node('validate', validate_infrastructure)
graph.add_node('deploy', deploy_depot_system)
graph.set_entry_point('validate')
graph.add_edge('validate', 'deploy')
graph.add_edge('deploy', END)
graph = graph.compile()
