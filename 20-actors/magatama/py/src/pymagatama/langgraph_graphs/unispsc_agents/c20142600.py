from typing import TypedDict
from langgraph.graph import StateGraph, END

class ActuatorState(TypedDict):
    specs: dict
    validated: bool
    error: str

def validate_specs(state: ActuatorState):
    required = ['load', 'stroke', 'accuracy']
    if all(k in state['specs'] for k in required):
        return {'validated': True}
    return {'validated': False, 'error': 'Missing required specs'}

workflow = StateGraph(ActuatorState)
workflow.add_node('validator', validate_specs)
workflow.set_entry_point('validator')
workflow.add_edge('validator', END)
graph = workflow.compile()