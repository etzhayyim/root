from typing import TypedDict
from langgraph.graph import StateGraph, END

class WorkflowState(TypedDict):
    sample_id: str
    validation_passed: bool
    device_status: str

def validate_hardware(state: WorkflowState):
    state['validation_passed'] = True
    state['device_status'] = 'READY'
    return state

def process_loading(state: WorkflowState):
    print(f'Loading sample {state["sample_id"]}')
    return {'device_status': 'PROCESSING'}

graph = StateGraph(WorkflowState)
graph.add_node('validate', validate_hardware)
graph.add_node('load', process_loading)
graph.set_entry_point('validate')
graph.add_edge('validate', 'load')
graph.add_edge('load', END)
graph = graph.compile()
