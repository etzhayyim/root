from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class PolymerState(TypedDict):
    material_id: str
    purity_level: float
    safety_clearance: bool
    compliance_checks: List[str]

def validate_chemistry(state: PolymerState):
    if state['purity_level'] > 0.98:
        return {'safety_clearance': True, 'compliance_checks': ['purity_ok']}
    return {'safety_clearance': False, 'compliance_checks': ['purity_fail']}

def route_by_safety(state: PolymerState):
    return 'process' if state['safety_clearance'] else END

def process_polymer(state: PolymerState):
    return {'compliance_checks': state['compliance_checks'] + ['thermal_stability_passed']}

graph = StateGraph(PolymerState)
graph.add_node('validate', validate_chemistry)
graph.add_node('process', process_polymer)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_safety)
graph.add_edge('process', END)
graph = graph.compile()
