from typing import TypedDict
from langgraph.graph import StateGraph, END

class ComponentState(TypedDict):
    alloy_grade: str
    dimensions: dict
    compliance_docs: list
    is_approved: bool

def validate_nickel_spec(state: ComponentState):
    # Business logic for nickel alloy compliance
    required_grades = ['N06625', 'N07718', 'N04400']
    valid = state['alloy_grade'] in required_grades
    return {'is_approved': valid}

graph = StateGraph(ComponentState)
graph.add_node('validation', validate_nickel_spec)
graph.add_edge('validation', END)
graph.set_entry_point('validation')
graph = graph.compile()
