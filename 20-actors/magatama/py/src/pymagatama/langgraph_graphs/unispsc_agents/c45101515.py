from typing import TypedDict
from langgraph.graph import StateGraph, END

class PrinterState(TypedDict):
    specs: dict
    validated: bool

def validate_specs(state: PrinterState):
    required = ['dpi', 'speed']
    state['validated'] = all(k in state['specs'] for k in required)
    return state

def assign_printer(state: PrinterState):
    print('Assigning printer to configuration queue...')
    return state

graph = StateGraph(PrinterState)
graph.add_node('validate', validate_specs)
graph.add_node('assign', assign_printer)
graph.add_edge('validate', 'assign')
graph.add_edge('assign', END)
graph.set_entry_point('validate')
graph = graph.compile()
