from typing import TypedDict
from langgraph.graph import StateGraph, END

class ScrewState(TypedDict):
    specifications: dict
    validation_passed: bool

def validate_compliance(state: ScrewState):
    required = ['material', 'thread_pitch']
    passed = all(k in state['specifications'] for k in required)
    return {'validation_passed': passed}

def finalize_order(state: ScrewState):
    print('Order processed for thread rolling screws.')
    return {'validation_passed': True}

graph = StateGraph(ScrewState)
graph.add_node('validate', validate_compliance)
graph.add_node('finalize', finalize_order)
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph.set_entry_point('validate')
graph = graph.compile()