from typing import TypedDict
from langgraph.graph import StateGraph, END

class PasteState(TypedDict):
    viscosity: float
    curing_agent: str
    is_compliant: bool

def validate_chemistry(state: PasteState) -> PasteState:
    state['is_compliant'] = state['viscosity'] > 0 and len(state['curing_agent']) > 0
    return state

def check_msds(state: PasteState) -> PasteState:
    print(f'Checking MSDS for chemistry: {state['curing_agent']}')
    return state

graph = StateGraph(PasteState)
graph.add_node('validate', validate_chemistry)
graph.add_node('msds_check', check_msds)
graph.set_entry_point('validate')
graph.add_edge('validate', 'msds_check')
graph.add_edge('msds_check', END)
graph = graph.compile()
