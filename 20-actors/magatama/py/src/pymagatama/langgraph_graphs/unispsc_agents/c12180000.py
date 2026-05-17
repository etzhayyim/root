from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
import operator

class CatalystState(TypedDict):
    batch_id: str
    purity: float
    safety_check: bool
    history: Annotated[List[str], operator.add]

def validate_catalyst(state: CatalystState):
    if state['purity'] >= 99.9:
        return {'safety_check': True, 'history': ['Purity validation passed']}
    return {'safety_check': False, 'history': ['Purity validation failed']}

def record_compliance(state: CatalystState):
    return {'history': ['Compliance record generated']}

builder = StateGraph(CatalystState)
builder.add_node('validate', validate_catalyst)
builder.add_node('record', record_compliance)
builder.add_edge('validate', 'record')
builder.add_edge('record', END)
builder.set_entry_point('validate')
graph = builder.compile()