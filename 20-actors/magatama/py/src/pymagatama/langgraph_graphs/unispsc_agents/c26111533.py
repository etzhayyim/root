from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ChainTensionerState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_approved: bool

def validate_specs(state: ChainTensionerState):
    required = ['Material', 'LoadCapacity']
    errors = [f'Missing {f}' for f in required if f not in state['spec_data']]
    return {'validation_errors': errors, 'is_approved': len(errors) == 0}

graph = StateGraph(ChainTensionerState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
