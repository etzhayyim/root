from typing import TypedDict
from langgraph.graph import StateGraph, END

class RivetState(TypedDict):
    spec_data: dict
    validation_passed: bool
    error_log: list

def validate_specs(state: RivetState):
    required = ['Material Grade', 'Diameter', 'Grip Range']
    errors = [f'Missing {f}' for f in required if f not in state['spec_data']]
    return {'validation_passed': len(errors) == 0, 'error_log': errors}

def finalize_order(state: RivetState):
    print('Order processed for compression rivets')
    return {'validation_passed': True}

graph = StateGraph(RivetState)
graph.add_node('validate', validate_specs)
graph.add_node('finalize', finalize_order)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()