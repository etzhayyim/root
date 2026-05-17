from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class TeaState(TypedDict):
    tea_data: dict
    quality_passed: bool
    validation_errors: List[str]

def validate_tea_quality(state: TeaState):
    errors = []
    if 'moisture' not in state['tea_data'] or state['tea_data']['moisture'] > 5.0:
        errors.append('High moisture content')
    return {'quality_passed': len(errors) == 0, 'validation_errors': errors}

def process_shipment(state: TeaState):
    return {'tea_data': {**state['tea_data'], 'status': 'processed'}}

builder = StateGraph(TeaState)
builder.add_node('validate', validate_tea_quality)
builder.add_node('process', process_shipment)
builder.set_entry_point('validate')
builder.add_edge('validate', 'process')
builder.add_edge('process', END)
graph = builder.compile()