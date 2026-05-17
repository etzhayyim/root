from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END

class SiliconState(TypedDict):
    purity: float
    inspection_passed: bool
    traceability_log: list

def validate_silicon_purity(state: SiliconState) -> dict:
    passed = state['purity'] >= 99.9999
    return {'inspection_passed': passed}

def update_log(state: SiliconState) -> dict:
    status = 'APPROVED' if state['inspection_passed'] else 'REJECTED'
    return {'traceability_log': state['traceability_log'] + [status]}

graph = StateGraph(SiliconState)
graph.add_node('validate', validate_silicon_purity)
graph.add_node('log', update_log)
graph.add_edge('validate', 'log')
graph.add_edge('log', END)
graph.set_entry_point('validate')
graph = graph.compile()