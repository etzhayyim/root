from typing import TypedDict
from langgraph.graph import StateGraph, END

class PrinterState(TypedDict):
    model_name: str
    specs: dict
    is_compliant: bool

def validate_specs(state: PrinterState):
    required_keys = ['dpi', 'ink_type']
    state['is_compliant'] = all(k in state['specs'] for k in required_keys)
    return state

def check_connectivity(state: PrinterState):
    if state.get('is_compliant'):
        print(f'Checking connectivity for {state[\'model_name\']}')
    return state

graph = StateGraph(PrinterState)
graph.add_node('validate', validate_specs)
graph.add_node('connectivity', check_connectivity)
graph.set_entry_point('validate')
graph.add_edge('validate', 'connectivity')
graph.add_edge('connectivity', END)
app = graph.compile()