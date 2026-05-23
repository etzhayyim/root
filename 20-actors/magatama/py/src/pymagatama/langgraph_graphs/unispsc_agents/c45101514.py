from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PrinterState(TypedDict):
    model_id: str
    specs: dict
    validation_passed: bool

def validate_specs(state: PrinterState):
    required_keys = ['voltage', 'print_area']
    passed = all(k in state['specs'] for k in required_keys)
    return {'validation_passed': passed}

def route_by_validation(state: PrinterState):
    return 'process' if state['validation_passed'] else END

def process_printer_workflow(state: PrinterState):
    print(f'Processing pad printer unit: {state.get('model_id')}')
    return {'validation_passed': True}

graph = StateGraph(PrinterState)
graph.add_node('validate', validate_specs)
graph.add_node('process', process_printer_workflow)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_validation)
graph.add_edge('process', END)
graph = graph.compile()
