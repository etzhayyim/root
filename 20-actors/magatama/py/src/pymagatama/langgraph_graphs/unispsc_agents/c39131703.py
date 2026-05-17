from typing import TypedDict
from langgraph.graph import StateGraph, END

class CableLadderState(TypedDict):
    load_capacity: float
    material: str
    is_compliant: bool

def validate_load_capacity(state: CableLadderState):
    state['is_compliant'] = state['load_capacity'] >= 500.0
    return state

def structural_check(state: CableLadderState):
    print(f'Checking material integrity for: {state["material"]}')
    return state

graph = StateGraph(CableLadderState)
graph.add_node('validate', validate_load_capacity)
graph.add_node('structural', structural_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'structural')
graph.add_edge('structural', END)
app = graph.compile()