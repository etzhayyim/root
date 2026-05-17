from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SquashProcureState(TypedDict):
    specs: dict
    validation_passed: bool
    errors: List[str]

def validate_specs(state: SquashProcureState):
    required = ['Weight', 'Frame Material']
    errors = [f'Missing {f}' for f in required if f not in state['specs']]
    return {'validation_passed': len(errors) == 0, 'errors': errors}

def finalize(state: SquashProcureState):
    print('Procurement specification validated for squash racquets.')
    return state

graph = StateGraph(SquashProcureState)
graph.add_node('validate', validate_specs)
graph.add_node('finalize', finalize)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()