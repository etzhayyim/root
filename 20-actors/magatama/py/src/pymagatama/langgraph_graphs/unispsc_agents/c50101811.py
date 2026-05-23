from typing import TypedDict
from langgraph.graph import StateGraph, END

class SatsumaState(TypedDict):
    brix_level: float
    shelf_life_days: int
    compliance_report: bool

def validate_quality(state: SatsumaState):
    if state['brix_level'] < 12.0:
        return {'status': 'rejected'}
    return {'status': 'approved'}

def check_compliance(state: SatsumaState):
    return {'compliant': state['compliance_report']}

graph = StateGraph(SatsumaState)
graph.add_node('validate', validate_quality)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
