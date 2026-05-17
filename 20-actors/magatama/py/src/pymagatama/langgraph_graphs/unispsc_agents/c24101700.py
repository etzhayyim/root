from typing import TypedDict
from langgraph.graph import StateGraph, END

class ConveyorState(TypedDict):
    specs: dict
    validation_status: str

def validate_specs(state: ConveyorState):
    required = ['load_capacity', 'safety_compliance']
    if all(k in state['specs'] for k in required):
        return {'validation_status': 'COMPLIANT'}
    return {'validation_status': 'PENDING_REVIEW'}

def route_by_validation(state: ConveyorState):
    return state['validation_status']

graph = StateGraph(ConveyorState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()