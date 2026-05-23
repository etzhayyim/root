from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class MineralState(TypedDict):
    purity: float
    particle_size: float
    compliance_docs: List[str]
    approved: bool

def validate_mineral(state: MineralState) -> MineralState:
    state['approved'] = state['purity'] >= 99.5 and len(state['compliance_docs']) > 0
    return state

def report_result(state: MineralState) -> MineralState:
    print(f'Mineral validation result: {state['approved']}')
    return state

graph = StateGraph(MineralState)
graph.add_node('validate', validate_mineral)
graph.add_node('report', report_result)
graph.set_entry_point('validate')
graph.add_edge('validate', 'report')
graph.add_edge('report', END)
graph = graph.compile()
