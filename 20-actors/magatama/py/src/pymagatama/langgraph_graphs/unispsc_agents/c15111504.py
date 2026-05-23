from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class RareEarthState(TypedDict):
    material_id: str
    purity: float
    analysis_report: dict
    approved: bool

def validate_purity(state: RareEarthState) -> RareEarthState:
    state['approved'] = state['purity'] >= 99.9
    return state

def check_regulations(state: RareEarthState) -> RareEarthState:
    if state['approved']:
        print(f'Compliance check passed for {state['material_id']}')
    return state

graph = StateGraph(RareEarthState)
graph.add_node('validate', validate_purity)
graph.add_node('compliance', check_regulations)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)

compiled_graph = graph.compile()
