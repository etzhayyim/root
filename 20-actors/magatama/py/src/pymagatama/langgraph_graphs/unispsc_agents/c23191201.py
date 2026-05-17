from typing import TypedDict
from langgraph.graph import StateGraph, END

class RobotProcessState(TypedDict):
    spec_data: dict
    validation_result: bool
    compliance_report: str

def validate_specs(state: RobotProcessState):
    specs = state['spec_data']
    valid = specs.get('payload_capacity_kg', 0) > 0 and specs.get('repeatability_tolerance_mm', 1) <= 0.5
    return {'validation_result': valid, 'compliance_report': 'Validated' if valid else 'Failed'}

def route_by_compliance(state: RobotProcessState):
    return 'process' if state['validation_result'] else END

graph = StateGraph(RobotProcessState)
graph.add_node('validate', validate_specs)
graph.add_node('process', lambda x: {'compliance_report': 'Proceeding to manufacturing integration'})
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_compliance)
graph.add_edge('process', END)
graph = graph.compile()