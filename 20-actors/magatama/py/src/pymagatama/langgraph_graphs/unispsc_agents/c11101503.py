from typing import TypedDict, Annotated, List, Union
from langgraph.graph import StateGraph, END
import operator

class BariteState(TypedDict):
    purity: float
    gravity: float
    inspection_report: str
    is_approved: bool
    history: Annotated[List[str], operator.add]

def validate_quality(state: BariteState) -> BariteState:
    approved = state['purity'] >= 95.0 and state['gravity'] >= 4.2
    return {'is_approved': approved, 'history': ['Validated quality metrics']}

def perform_audit(state: BariteState) -> BariteState:
    return {'history': ['Completed technical compliance audit']}

def route_by_approval(state: BariteState) -> str:
    return 'audit' if state['is_approved'] else END

graph = StateGraph(BariteState)
graph.add_node('validate', validate_quality)
graph.add_node('audit', perform_audit)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_approval)
graph.add_edge('audit', END)
graph = graph.compile()