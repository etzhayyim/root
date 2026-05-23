from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class LabBridgeState(TypedDict):
    specifications: dict
    validation_passed: bool
    errors: List[str]

def validate_specs(state: LabBridgeState):
    errors = []
    if state['specifications'].get('load_capacity_kg', 0) <= 0:
        errors.append('Invalid load capacity')
    return {'validation_passed': len(errors) == 0, 'errors': errors}

def process_procurement(state: LabBridgeState):
    print('Processing laboratory bridge procurement...')
    return state

workflow = StateGraph(LabBridgeState)
workflow.add_node('validate', validate_specs)
workflow.add_node('process', process_procurement)
workflow.add_edge('validate', 'process')
workflow.add_edge('process', END)
workflow.set_entry_point('validate')
graph = workflow.compile()
