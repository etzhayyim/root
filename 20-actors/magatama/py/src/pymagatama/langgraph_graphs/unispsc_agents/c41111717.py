from typing import TypedDict
from langgraph.graph import StateGraph, END

class BinocularState(TypedDict):
    specs: dict
    is_compliant: bool

def validate_optics(state: BinocularState):
    specs = state['specs']
    valid = specs.get('magnification', 0) > 0 and 'coating' in specs
    return {'is_compliant': valid}

def export_check(state: BinocularState):
    print('Checking dual-use export regulations...')
    return {}

builder = StateGraph(BinocularState)
builder.add_node('validate', validate_optics)
builder.add_node('export_review', export_check)
builder.set_entry_point('validate')
builder.add_edge('validate', 'export_review')
builder.add_edge('export_review', END)
graph = builder.compile()
