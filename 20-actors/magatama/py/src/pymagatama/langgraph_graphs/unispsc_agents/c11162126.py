from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class PolysiliconState(TypedDict):
    batch_id: str
    purity_level: float
    inspection_passed: bool
    log: List[str]

def validate_purity(state: PolysiliconState):
    passed = state['purity_level'] >= 99.9999999
    return {'inspection_passed': passed, 'log': state['log'] + ['Purity validation completed']}

def process_batch(state: PolysiliconState):
    if state['inspection_passed']:
        return {'log': state['log'] + ['Batch cleared for semiconductor fabrication']}
    else:
        return {'log': state['log'] + ['Batch rejected for insufficient purity']}

builder = StateGraph(PolysiliconState)
builder.add_node('validate', validate_purity)
builder.add_node('process', process_batch)
builder.add_edge('validate', 'process')
builder.add_edge('process', END)
builder.set_entry_point('validate')
graph = builder.compile()