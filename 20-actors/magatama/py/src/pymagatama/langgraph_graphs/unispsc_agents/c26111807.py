from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class TimingPulleyState(TypedDict):
    specs: dict
    validation_passed: bool
    errors: List[str]

def validate_specs(state: TimingPulleyState):
    required = ['pitch', 'bore', 'teeth']
    errors = []
    for field in required:
        if field not in state['specs']:
            errors.append(f'Missing {field}')
    return {'validation_passed': len(errors) == 0, 'errors': errors}

def process_procurement(state: TimingPulleyState):
    if state['validation_passed']:
        print('Proceeding to procurement order generation')
    return {}

graph = StateGraph(TimingPulleyState)
graph.add_node('validate', validate_specs)
graph.add_node('order', process_procurement)
graph.add_edge('validate', 'order')
graph.add_edge('order', END)
graph.set_entry_point('validate')
graph = graph.compile()