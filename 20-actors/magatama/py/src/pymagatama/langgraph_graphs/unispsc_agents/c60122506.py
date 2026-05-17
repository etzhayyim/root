from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    spec_data: dict
    approved: bool

def validate_food_grade(state: ProcurementState):
    is_safe = state['spec_data'].get('food_grade_cert') is True
    return {'approved': is_safe}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_food_grade)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()