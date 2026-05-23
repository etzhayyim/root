from typing import TypedDict
from langgraph.graph import StateGraph, END

class HeaterProcessState(TypedDict):
    voltage: float
    target_temp: float
    safety_check: bool

def validate_specs(state: HeaterProcessState):
    print('Validating thermal specs...')
    return {'safety_check': state['target_temp'] < 800}

def approval_step(state: HeaterProcessState):
    print('Checking compliance...')
    return {'safety_check': True}

graph = StateGraph(HeaterProcessState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_step)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()
