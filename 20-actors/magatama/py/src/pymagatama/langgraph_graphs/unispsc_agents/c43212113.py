from langgraph.graph import StateGraph, END
from typing import TypedDict

class PrinterState(TypedDict):
    specs: dict
    validated: bool
    error: str

def validate_specs(state: PrinterState):
    required = ['DPI', 'format']
    if all(k in state['specs'] for k in required):
        return {'validated': True}
    return {'validated': False, 'error': 'Missing specs'}

workflow = StateGraph(PrinterState)
workflow.add_node('validate', validate_specs)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()