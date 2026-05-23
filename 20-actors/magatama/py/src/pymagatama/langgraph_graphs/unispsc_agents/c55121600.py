from typing import TypedDict
from langgraph.graph import StateGraph, END

class LabelState(TypedDict):
    spec_data: dict
    validation_status: bool
    error_logs: list

def validate_specs(state: LabelState):
    required = ['material', 'dimensions', 'adhesive_type']
    valid = all(k in state['spec_data'] for k in required)
    return {'validation_status': valid, 'error_logs': [] if valid else ['Missing technical specs']}

def finalize_order(state: LabelState):
    if state['validation_status']:
        print('Label specifications approved for procurement.')
    return {}

graph = StateGraph(LabelState)
graph.add_node('validate', validate_specs)
graph.add_node('finalize', finalize_order)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()
