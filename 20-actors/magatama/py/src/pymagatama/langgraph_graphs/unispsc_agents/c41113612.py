from typing import TypedDict
from langgraph.graph import StateGraph, END

class TesterState(TypedDict):
    spec: dict
    validated: bool
    error: str

def validate_specs(state: TesterState):
    required = ['accuracy_tolerance', 'calibration_standard_compliance']
    valid = all(k in state['spec'] for k in required)
    return {'validated': valid}

def process_workflow(state: TesterState):
    if state['validated']:
        print('Processing technical validation for earth resistance tester.')
    return {'error': 'None' if state['validated'] else 'Missing Spec'}

graph = StateGraph(TesterState)
graph.add_node('validate', validate_specs)
graph.add_node('process', process_workflow)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph = graph.compile()