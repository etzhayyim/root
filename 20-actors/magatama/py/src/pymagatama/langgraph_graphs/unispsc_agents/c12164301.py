from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class LubricantState(TypedDict):
    lubricant_id: str
    viscosity: float
    temp_range: tuple
    compliance_checks: Annotated[Sequence[str], operator.add]
    is_approved: bool

def validate_viscosity(state: LubricantState):
    # Business logic for viscosity validation
    is_ok = state['viscosity'] > 0
    return {'compliance_checks': ['viscosity_validated'] if is_ok else ['viscosity_failed'], 'is_approved': is_ok}

def safety_review(state: LubricantState):
    # Logic for safety review against dangerous goods threshold
    return {'compliance_checks': ['safety_reviewed']}

def build_graph():
    graph = StateGraph(LubricantState)
    graph.add_node('validate', validate_viscosity)
    graph.add_node('safety', safety_review)
    graph.set_entry_point('validate')
    graph.add_edge('validate', 'safety')
    graph.add_edge('safety', END)
    return graph.compile()

graph = build_graph()