from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
import operator

class CatalystState(TypedDict):
    purity: float
    surface_area: float
    compliance_checks: Annotated[List[str], operator.add]
    status: str

def validate_purity(state: CatalystState):
    status = 'approved' if state['purity'] >= 99.9 else 'rejected'
    return {'status': status, 'compliance_checks': ['purity_verified']}

def check_hazard_classification(state: CatalystState):
    return {'compliance_checks': ['hazmat_protocol_active']}

graph = StateGraph(CatalystState)
graph.add_node('validate', validate_purity)
graph.add_node('hazard_check', check_hazard_classification)
graph.set_entry_point('validate')
graph.add_edge('validate', 'hazard_check')
graph.add_edge('hazard_check', END)

compile_graph = graph.compile()
