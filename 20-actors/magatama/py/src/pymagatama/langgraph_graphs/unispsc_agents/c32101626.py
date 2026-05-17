from typing import TypedDict
from langgraph.graph import StateGraph, END

class MicroprocessorState(TypedDict):
    specs: dict
    validated: bool
    export_compliant: bool

def validate_tech(state: MicroprocessorState):
    print('Validating hardware specifications...')
    state['validated'] = state['specs'].get('lithography', 0) < 10
    return state

def check_compliance(state: MicroprocessorState):
    print('Checking export/dual-use compliance...')
    state['export_compliant'] = state['specs'].get('eccn') is not None
    return state

graph = StateGraph(MicroprocessorState)
graph.add_node('validate_tech', validate_tech)
graph.add_node('check_compliance', check_compliance)
graph.set_entry_point('validate_tech')
graph.add_edge('validate_tech', 'check_compliance')
graph.add_edge('check_compliance', END)
graph = graph.compile()