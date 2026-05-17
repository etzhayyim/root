from typing import TypedDict
from langgraph.graph import StateGraph, END

class LabelState(TypedDict):
    spec: dict
    validated: bool

def validate_specs(state: LabelState):
    required = ['adhesive_type', 'printer_type', 'size']
    state['validated'] = all(k in state['spec'] for k in required)
    return state

def route_by_validation(state: LabelState):
    return 'process' if state['validated'] else END

def process_label_order(state: LabelState):
    print('Processing label procurement parameters...')
    return state

builder = StateGraph(LabelState)
builder.add_node('validate', validate_specs)
builder.add_node('process', process_label_order)
builder.add_edge('validate', 'process')
builder.set_entry_point('validate')
builder.add_edge('process', END)
graph = builder.compile()