from typing import TypedDict
from langgraph.graph import StateGraph, END

class BrakeRotorState(TypedDict):
    specs: dict
    validated: bool
    error: str

def validate_specs(state: BrakeRotorState):
    required = ['diameter', 'thickness', 'material']
    if all(k in state['specs'] for k in required):
        return {'validated': True}
    return {'validated': False, 'error': 'Missing core specifications.'}

workflow = StateGraph(BrakeRotorState)
workflow.add_node('validate', validate_specs)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()