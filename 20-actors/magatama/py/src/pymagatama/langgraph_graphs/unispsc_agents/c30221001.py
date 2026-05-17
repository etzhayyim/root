from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class MallProcurementState(TypedDict):
    facility_id: str
    compliance_docs: List[str]
    status: str

def validate_permits(state: MallProcurementState):
    print(f'Validating permits for {state['facility_id']}')
    return {'status': 'Permits Validated'}

def perform_audit(state: MallProcurementState):
    print('Performing facility management audit')
    return {'status': 'Audit Completed'}

graph = StateGraph(MallProcurementState)
graph.add_node('validate', validate_permits)
graph.add_node('audit', perform_audit)
graph.set_entry_point('validate')
graph.add_edge('validate', 'audit')
graph.add_edge('audit', END)
app = graph.compile()