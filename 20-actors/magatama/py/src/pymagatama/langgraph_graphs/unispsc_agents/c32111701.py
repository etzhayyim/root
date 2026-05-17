from typing import TypedDict
from langgraph.graph import StateGraph, END

class PVState(TypedDict):
    specs: dict
    validation_passed: bool

def validate_specs(state: PVState):
    efficiency = state['specs'].get('efficiency', 0)
    if efficiency >= 0.20:
        return {'validation_passed': True}
    return {'validation_passed': False}

def update_status(state: PVState):
    print(f"Validation status: {state['validation_passed']}")
    return state

graph = StateGraph(PVState)
graph.add_node('validate', validate_specs)
graph.add_node('status', update_status)
graph.set_entry_point('validate')
graph.add_edge('validate', 'status')
graph.add_edge('status', END)
graph = graph.compile()