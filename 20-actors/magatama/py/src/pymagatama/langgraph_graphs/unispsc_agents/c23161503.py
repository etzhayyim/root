from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class RobotControllerState(TypedDict):
    controller_id: str
    specs: dict
    is_validated: bool
    compliance_report: List[str]

def validate_specs(state: RobotControllerState):
    # Business logic for spec validation
    iso_req = state['specs'].get('safety_cert') == 'ISO-10218'
    return {'is_validated': iso_req, 'compliance_report': ['ISO-10218 validated'] if iso_req else ['Validation Failed']}

def route_by_validation(state: RobotControllerState):
    return 'process' if state['is_validated'] else END

graph = StateGraph(RobotControllerState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_validation, {'process': END})
graph.add_edge('validate', END)

app = graph.compile()
