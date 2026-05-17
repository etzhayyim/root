from typing import TypedDict
from langgraph.graph import StateGraph, END

class PrinterState(TypedDict):
    specs: dict
    validation_status: str

def validate_specs(state: PrinterState):
    required = ['speed', 'barcode_types']
    all_present = all(k in state['specs'] for k in required)
    state['validation_status'] = 'COMPLIANT' if all_present else 'INCOMPLETE'
    return state

def check_compatibility(state: PrinterState):
    if state['validation_status'] == 'COMPLIANT':
        state['validation_status'] = 'READY_FOR_PROCUREMENT'
    return state

graph = StateGraph(PrinterState)
graph.add_node('validator', validate_specs)
graph.add_node('compatibility', check_compatibility)
graph.set_entry_point('validator')
graph.add_edge('validator', 'compatibility')
graph.add_edge('compatibility', END)
graph = graph.compile()