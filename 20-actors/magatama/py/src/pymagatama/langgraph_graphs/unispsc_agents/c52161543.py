from typing import TypedDict
from langgraph.graph import StateGraph, END

class MP3ProcessorState(TypedDict):
    device_id: str
    specs: dict
    validation_status: bool

def validate_specs(state: MP3ProcessorState):
    required = ['storage_capacity_gb', 'supported_file_formats']
    state['validation_status'] = all(k in state['specs'] for k in required)
    return state

def run_compliance_check(state: MP3ProcessorState):
    print(f'Checking compliance for {state['device_id']}')
    return state

graph = StateGraph(MP3ProcessorState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', run_compliance_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
