from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class MineralState(TypedDict):
    purity: float
    spec_compliant: bool
    history: List[str]

def validate_purity(state: MineralState) -> MineralState:
    compliant = state['purity'] >= 99.5
    return {**state, 'spec_compliant': compliant, 'history': state['history'] + ['purity_check']}

def process_mineral(state: MineralState) -> MineralState:
    return {**state, 'history': state['history'] + ['processing_complete']}

graph = StateGraph(MineralState)
graph.add_node('validate', validate_purity)
graph.add_node('process', process_mineral)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph = graph.compile()