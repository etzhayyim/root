from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ConcentrateState(TypedDict):
    brix: float
    safety_check: bool
    approved: bool

def validate_quality(state: ConcentrateState) -> ConcentrateState:
    state['approved'] = state['brix'] >= 45.0 and state['safety_check']
    return state

def report_status(state: ConcentrateState) -> dict:
    return {'status': 'Approved' if state['approved'] else 'Rejected'}

graph_builder = StateGraph(ConcentrateState)
graph_builder.add_node('validate', validate_quality)
graph_builder.add_node('report', report_status)
graph_builder.set_entry_point('validate')
graph_builder.add_edge('validate', 'report')
graph_builder.add_edge('report', END)
graph = graph_builder.compile()