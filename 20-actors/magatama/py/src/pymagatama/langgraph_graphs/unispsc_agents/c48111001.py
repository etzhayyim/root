from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class VendingMachineState(TypedDict):
    model_id: str
    specs: dict
    validation_errors: List[str]
    is_approved: bool

def validate_specs(state: VendingMachineState):
    errors = []
    if state['specs'].get('power_consumption_kwh', 0) > 2.0:
        errors.append('Exceeds energy efficiency threshold')
    return {'validation_errors': errors}

def check_compliance(state: VendingMachineState):
    is_valid = len(state['validation_errors']) == 0
    return {'is_approved': is_valid}

graph = StateGraph(VendingMachineState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()
