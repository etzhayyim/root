from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ResinState(TypedDict):
    batch_id: str
    specs: dict
    validation_passed: bool
    log: List[str]

def validate_specs(state: ResinState):
    passed = state['specs'].get('tensile_strength_mpa', 0) > 500
    return {'validation_passed': passed, 'log': [f'Validation: {passed}']}

def process_resin(state: ResinState):
    return {'log': state['log'] + ['Processing through high-pressure injection molding validation.']}

builder = StateGraph(ResinState)
builder.add_node('validate', validate_specs)
builder.add_node('process', process_resin)
builder.set_entry_point('validate')
builder.add_edge('validate', 'process')
builder.add_edge('process', END)
graph = builder.compile()