from typing import TypedDict
from langgraph.graph import StateGraph, END

class PrinterState(TypedDict):
    model_specs: dict
    compliance_verified: bool
    approved: bool

def validate_specs(state: PrinterState):
    required = ['speed', 'dpi', 'duty_cycle']
    state['compliance_verified'] = all(k in state['model_specs'] for k in required)
    return state

def check_approval(state: PrinterState):
    state['approved'] = state['compliance_verified'] and state['model_specs'].get('energy_star', False)
    return state

graph = StateGraph(PrinterState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', check_approval)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()