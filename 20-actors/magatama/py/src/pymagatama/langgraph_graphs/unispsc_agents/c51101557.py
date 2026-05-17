from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ReagentState(TypedDict):
    reagent_id: str
    quality_metrics: dict
    workflow_stage: str
    approval_status: bool

def validate_purity(state: ReagentState):
    purity = state['quality_metrics'].get('purity', 0)
    return {'approval_status': purity >= 99.9}

def process_logistics(state: ReagentState):
    return {'workflow_stage': 'logistics_complete'}

builder = StateGraph(ReagentState)
builder.add_node('validate', validate_purity)
builder.add_node('logistics', process_logistics)
builder.add_edge('validate', 'logistics')
builder.add_edge('logistics', END)
builder.set_entry_point('validate')
graph = builder.compile()