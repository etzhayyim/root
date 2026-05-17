from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
import operator

class CouplingState(TypedDict):
    spec_requirements: dict
    validation_results: List[str]
    is_compliant: bool

def validate_torque(state: CouplingState) -> CouplingState:
    torque = state['spec_requirements'].get('torque_rating_nm', 0)
    if torque > 0:
        state['validation_results'].append(f'Torque verified: {torque}Nm')
    return state

def check_compliance(state: CouplingState) -> CouplingState:
    state['is_compliant'] = len(state['validation_results']) > 0
    return state

graph = StateGraph(CouplingState)
graph.add_node('torque_check', validate_torque)
graph.add_node('compliance_check', check_compliance)
graph.set_entry_point('torque_check')
graph.add_edge('torque_check', 'compliance_check')
graph.add_edge('compliance_check', END)
graph = graph.compile()