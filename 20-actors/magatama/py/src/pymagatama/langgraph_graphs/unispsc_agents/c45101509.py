from typing import TypedDict
from langgraph.graph import StateGraph, END

class PrinterState(TypedDict):
    specs: dict
    is_validated: bool

def validate_specs(state: PrinterState):
    diameter = state['specs'].get('diameter', 0)
    state['is_validated'] = 0 < diameter < 500
    return state

def check_compliance(state: PrinterState):
    return {'is_validated': state['is_validated'] and 'CE' in state['specs'].get('certs', [])}

graph = StateGraph(PrinterState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
