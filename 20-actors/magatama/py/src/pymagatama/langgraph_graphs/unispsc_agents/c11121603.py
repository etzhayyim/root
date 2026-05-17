from typing import TypedDict, Annotated, List, Any
from langgraph.graph import StateGraph, END

class AluminumIngotState(TypedDict):
    purity: float
    alloy_elements: dict
    tensile_strength: float
    status: str

def validate_material(state: AluminumIngotState) -> AluminumIngotState:
    if state['purity'] < 99.9:
        state['status'] = 'REJECTED: Low Purity'
    else:
        state['status'] = 'VALIDATED'
    return state

def check_compliance(state: AluminumIngotState) -> AluminumIngotState:
    if state['status'] == 'VALIDATED':
        if state['tensile_strength'] < 400:
            state['status'] = 'REJECTED: Insufficient Strength'
    return state

graph = StateGraph(AluminumIngotState)
graph.add_node('validate', validate_material)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)

compiled_graph = graph.compile()