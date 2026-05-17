from typing import TypedDict
from langgraph.graph import StateGraph, END

class SocketState(TypedDict):
    specs: dict
    is_compliant: bool
    validation_log: list

def validate_specs(state: SocketState):
    required = ['voltage', 'base_type', 'certifications']
    missing = [f for f in required if f not in state['specs']]
    is_valid = len(missing) == 0
    return {'is_compliant': is_valid, 'validation_log': [f'Missing: {missing}'] if missing else ['OK']}

workflow = StateGraph(SocketState)
workflow.add_node('validate', validate_specs)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()