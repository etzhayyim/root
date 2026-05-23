from typing import TypedDict
from langgraph.graph import StateGraph, END

class MoldState(TypedDict):
    spec_data: dict
    validation_result: bool

def validate_casting_specs(state: MoldState):
    required = ['Material', 'Tolerance']
    result = all(k in state['spec_data'] for k in required)
    return {'validation_result': result}

def process_casting(state: MoldState):
    print('Processing casting quality standards...')
    return {'validation_result': True}

graph = StateGraph(MoldState)
graph.add_node('validate', validate_casting_specs)
graph.add_node('process', process_casting)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph = graph.compile()
