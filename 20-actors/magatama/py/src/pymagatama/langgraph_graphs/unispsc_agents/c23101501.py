from typing import TypedDict
from langgraph.graph import StateGraph, END

class CompressorState(TypedDict):
    spec_data: dict
    validation_result: bool
    error_log: list

def validate_specs(state: CompressorState):
    required = ['pressure', 'power', 'flow']
    errors = [key for key in required if key not in state['spec_data']]
    return {'validation_result': len(errors) == 0, 'error_log': errors}

def approval_step(state: CompressorState):
    print('Proceeding to technical approval.')
    return {'validation_result': True}

graph = StateGraph(CompressorState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_step)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()
