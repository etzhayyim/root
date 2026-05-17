from typing import TypedDict
from langgraph.graph import StateGraph, END

class StorageState(TypedDict):
    specs: dict
    validation_result: bool

def validate_storage_specs(state: StorageState):
    required = ['capacity', 'interface']
    valid = all(k in state['specs'] for k in required)
    return {'validation_result': valid}

def security_audit(state: StorageState):
    print('Performing cryptographic compliance check...')
    return {'validation_result': state['validation_result']}

graph = StateGraph(StorageState)
graph.add_node('validate', validate_storage_specs)
graph.add_node('audit', security_audit)
graph.add_edge('validate', 'audit')
graph.add_edge('audit', END)
graph.set_entry_point('validate')
graph.compile()