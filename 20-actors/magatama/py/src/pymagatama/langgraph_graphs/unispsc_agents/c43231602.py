from typing import TypedDict
from langgraph.graph import StateGraph, END

class ERPState(TypedDict):
    requirements: dict
    validation_report: dict
    is_compliant: bool

def validate_erp_specs(state: ERPState):
    # Simulate business rule validation for ERP procurement
    required_keys = ['cloud_security', 'scalability', 'data_sovereignty']
    compliance = all(k in state['requirements'] for k in required_keys)
    return {'validation_report': {'status': 'success' if compliance else 'fail'}, 'is_compliant': compliance}

def deploy_procurement_task(state: ERPState):
    return {'validation_report': {'msg': 'Ready for RFP release'}}

graph = StateGraph(ERPState)
graph.add_node('validate', validate_erp_specs)
graph.add_node('deploy', deploy_procurement_task)
graph.set_entry_point('validate')
graph.add_edge('validate', 'deploy')
graph.add_edge('deploy', END)
graph = graph.compile()