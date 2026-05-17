from typing import TypedDict
from langgraph.graph import StateGraph, END

class IRState(TypedDict):
    specs: dict
    validated: bool
    export_cleared: bool

def validate_specs(state: IRState):
    cooling_cap = state['specs'].get('cooling_cap', 0)
    state['validated'] = cooling_cap > 0
    return state

def check_export(state: IRState):
    eccn = state['specs'].get('eccn', '')
    state['export_cleared'] = eccn == '6A002'
    return state

graph = StateGraph(IRState)
graph.add_node('validate_specs', validate_specs)
graph.add_node('check_export', check_export)
graph.set_entry_point('validate_specs')
graph.add_edge('validate_specs', 'check_export')
graph.add_edge('check_export', END)

graph = graph.compile()