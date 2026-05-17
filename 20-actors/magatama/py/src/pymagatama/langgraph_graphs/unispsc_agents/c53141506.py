from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SnapState(TypedDict):
    snap_type: str
    pull_test_n: float
    passes_qc: bool

def validate_snap_strength(state: SnapState):
    state['passes_qc'] = state['pull_test_n'] >= 70.0
    return state

def handle_quality_report(state: SnapState):
    print(f'Snap QC Status: {state['passes_qc']}')
    return state

graph = StateGraph(SnapState)
graph.add_node('validate', validate_snap_strength)
graph.add_node('report', handle_quality_report)
graph.add_edge('validate', 'report')
graph.add_edge('report', END)
graph.set_entry_point('validate')
graph = graph.compile()