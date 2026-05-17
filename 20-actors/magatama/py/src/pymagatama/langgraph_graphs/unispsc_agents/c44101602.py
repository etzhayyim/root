from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BindingMachineState(TypedDict):
    model_id: str
    specs: dict
    validation_passed: bool
    errors: List[str]

def validate_specs(state: BindingMachineState):
    errors = []
    if state['specs'].get('binding_capacity', 0) <= 0:
        errors.append('Invalid binding capacity')
    return {'validation_passed': len(errors) == 0, 'errors': errors}

def process_procurement(state: BindingMachineState):
    print(f'Processing procurement for {state['model_id']}')
    return state

graph = StateGraph(BindingMachineState)
graph.add_node('validate', validate_specs)
graph.add_node('process', process_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph = graph.compile()