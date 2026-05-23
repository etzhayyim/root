from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
import operator

class CrudeOilState(TypedDict):
    batch_id: str
    gravity: float
    sulfur: float
    status: str
    logs: Annotated[list[str], operator.add]

def validate_chemistry(state: CrudeOilState) -> CrudeOilState:
    if state['sulfur'] > 0.5:
        return {'status': 'REJECTED_SULFUR_TOO_HIGH', 'logs': ['Sulfur content exceeds threshold']}
    return {'status': 'VALIDATED', 'logs': ['Chemistry check passed']}

def check_compliance(state: CrudeOilState) -> CrudeOilState:
    if state['status'] != 'VALIDATED': return state
    return {'status': 'COMPLIANCE_CLEARED', 'logs': ['Sanctions screening passed']}

graph = StateGraph(CrudeOilState)
graph.add_node('chemistry', validate_chemistry)
graph.add_node('compliance', check_compliance)
graph.add_edge('chemistry', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('chemistry')
graph = graph.compile()
