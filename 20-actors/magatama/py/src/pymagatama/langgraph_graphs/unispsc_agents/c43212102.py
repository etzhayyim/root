from typing import TypedDict
from langgraph.graph import StateGraph, END

class PrinterState(TypedDict):
    specs: dict
    is_validated: bool

def validate_specs(state: PrinterState):
    required = ['pin_config', 'interface']
    valid = all(k in state['specs'] for k in required)
    return {'is_validated': valid}

def printer_check(state: PrinterState):
    print('Validating Dot Matrix technical parameters...')
    return 'validated'

graph = StateGraph(PrinterState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()
