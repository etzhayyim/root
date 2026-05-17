from typing import TypedDict, Annotated, List, Dict, Any
from langgraph.graph import StateGraph, END

class RobotProcurementState(TypedDict):
    spec_requirements: Dict[str, Any]
    validation_results: List[str]
    compliance_score: float

def validate_specs(state: RobotProcurementState) -> RobotProcurementState:
    specs = state['spec_requirements']
    results = []
    if specs.get('payload_capacity_kg', 0) <= 0:
        results.append('Payload capacity must be positive.')
    state['validation_results'] = results
    return state

def check_compliance(state: RobotProcurementState) -> RobotProcurementState:
    state['compliance_score'] = 1.0 if not state['validation_results'] else 0.0
    return state

graph = StateGraph(RobotProcurementState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
robot_procurement_graph = graph.compile()