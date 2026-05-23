from typing import TypedDict
from langgraph.graph import StateGraph, END

class BeltState(TypedDict):
    specs: dict
    validation_result: bool
    error_log: list

def validate_specs(state: BeltState):
    required = ['pitch', 'width', 'material']
    missing = [f for f in required if f not in state['specs']]
    return {'validation_result': len(missing) == 0, 'error_log': missing}

def process_belt(state: BeltState):
    print('Processing timing belt technical documentation...')
    return state

graph = StateGraph(BeltState)
graph.add_node('validate', validate_specs)
graph.add_node('process', process_belt)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph = graph.compile()
