from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class PaperPalletState(TypedDict):
    spec_data: dict
    validation_logs: List[str]
    is_compliant: bool

def validate_load_capacity(state: PaperPalletState) -> PaperPalletState:
    load = state['spec_data'].get('load_capacity_kg', 0)
    if load < 500:
        state['validation_logs'].append('Critical: Load capacity below safety standard.')
        state['is_compliant'] = False
    return state

def check_sustainability(state: PaperPalletState) -> PaperPalletState:
    if not state['spec_data'].get('recyclability_index', 0) > 80:
        state['validation_logs'].append('Warning: Recyclability score suboptimal.')
    return state

builder = StateGraph(PaperPalletState)
builder.add_node('validate_load', validate_load_capacity)
builder.add_node('check_eco', check_sustainability)
builder.set_entry_point('validate_load')
builder.add_edge('validate_load', 'check_eco')
builder.add_edge('check_eco', END)
graph = builder.compile()
