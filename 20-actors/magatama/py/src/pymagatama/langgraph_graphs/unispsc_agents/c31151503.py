from typing import TypedDict
from langgraph.graph import StateGraph, END

class RopeSpecState(TypedDict):
    spec_data: dict
    validated: bool
    error_log: list

def validate_specs(state: RopeSpecState):
    required = ['tensile_strength', 'diameter', 'length']
    errors = [f'Missing {f}' for f in required if f not in state['spec_data']]
    return {'validated': len(errors) == 0, 'error_log': errors}

workflow = StateGraph(RopeSpecState)
workflow.add_node('validate', validate_specs)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()
