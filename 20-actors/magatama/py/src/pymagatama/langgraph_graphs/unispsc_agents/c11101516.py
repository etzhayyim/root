from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class MineralState(TypedDict):
    batch_id: str
    purity: float
    analysis_report: dict
    is_compliant: bool

def validate_batch(state: MineralState) -> dict:
    is_valid = state['purity'] >= 99.9
    return {'is_compliant': is_valid}

def process_batch(state: MineralState) -> dict:
    return {'batch_id': f'PROC-{state['batch_id']}'}

graph = StateGraph(MineralState)
graph.add_node('validate', validate_batch)
graph.add_node('process', process_batch)
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')
graph = graph.compile()