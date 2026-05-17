from langgraph.graph import StateGraph, END
from typing import TypedDict

class ProcurementState(TypedDict):
    spec_data: dict
    compliance_score: float
    approved: bool

def validate_food_grade(state: ProcurementState):
    # Simulate food safety compliance check
    compliance = state['spec_data'].get('food_safe', False)
    return {'compliance_score': 1.0 if compliance else 0.0, 'approved': compliance}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_food_grade)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()