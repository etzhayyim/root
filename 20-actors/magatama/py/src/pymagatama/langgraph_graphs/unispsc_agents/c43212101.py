from typing import TypedDict
from langgraph.graph import StateGraph, END
class PrinterState(TypedDict):
    model_id: str
    specs: dict
    is_validated: bool
def validate_band_printer(state: PrinterState):
    required_fields = ['lpm', 'paper_width']
    state['is_validated'] = all(k in state['specs'] for k in required_fields)
    return state
def route_verification(state: PrinterState):
    return 'valid' if state['is_validated'] else 'invalid'
graph = StateGraph(PrinterState)
graph.add_node('validate', validate_band_printer)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
