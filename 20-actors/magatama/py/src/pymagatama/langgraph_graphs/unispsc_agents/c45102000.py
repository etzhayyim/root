from typing import TypedDict
from langgraph.graph import StateGraph, END

class ComposingState(TypedDict):
    specs: dict
    validation_status: bool

def validate_specs(state: ComposingState):
    # Business logic for confirming hardware and software compatibility
    state['validation_status'] = 'processor_type' in state['specs'] and 'os_version' in state['specs']
    return 'validated' if state['validation_status'] else 'error'

def finalize_order(state: ComposingState):
    return {'validation_status': True}

graph = StateGraph(ComposingState)
graph.add_node('validate', validate_specs)
graph.add_node('finalize', finalize_order)
graph.add_edge('validate', 'finalize')
graph.set_entry_point('validate')
graph.add_edge('finalize', END)
graph = graph.compile()