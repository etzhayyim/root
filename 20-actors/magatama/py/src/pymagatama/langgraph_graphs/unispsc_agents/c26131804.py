from typing import TypedDict
from langgraph.graph import StateGraph, END
class TurbineControlState(TypedDict):
    spec_data: dict
    validation_status: bool
    compliance_report: str
def validate_specs(state: TurbineControlState):
    fields = ['voltage_rating', 'nema_rating', 'communication_protocol']
    is_valid = all(key in state['spec_data'] for key in fields)
    return {'validation_status': is_valid, 'compliance_report': 'Success' if is_valid else 'Missing mandatory specs'}
def finalize_workflow(state: TurbineControlState):
    return {'compliance_report': 'Workflow Completed: Final Review Registered'}
graph = StateGraph(TurbineControlState)
graph.add_node('validate', validate_specs)
graph.add_node('finalize', finalize_workflow)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()
