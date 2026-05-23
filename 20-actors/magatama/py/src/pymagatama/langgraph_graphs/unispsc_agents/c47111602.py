from typing import TypedDict
from langgraph.graph import StateGraph, END

class FoldingMachineState(TypedDict):
    model_number: str
    spec_sheet: dict
    validation_passed: bool

def validate_specs(state: FoldingMachineState):
    required = ['speed', 'paper_weight']
    passed = all(k in state['spec_sheet'] for k in required)
    return {'validation_passed': passed}

def route_by_validation(state: FoldingMachineState):
    return 'process' if state['validation_passed'] else END

graph = StateGraph(FoldingMachineState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_validation, {'process': 'process', '__end__': END})
graph.add_node('process', lambda s: {'model_number': s['model_number']})
graph.add_edge('process', END)
graph = graph.compile()
