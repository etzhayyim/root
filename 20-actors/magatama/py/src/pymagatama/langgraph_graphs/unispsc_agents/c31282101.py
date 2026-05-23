from typing import TypedDict
from langgraph.graph import StateGraph, END

class SpinFormState(TypedDict):
    specs: dict
    validated: bool
    error: str

def validate_specs(state: SpinFormState):
    required = ['alloy', 'thickness', 'tolerance']
    if all(k in state['specs'] for k in required):
        return {'validated': True}
    return {'validated': False, 'error': 'Missing required technical specs'}

def process_manufacturing(state: SpinFormState):
    print('Initiating CAD check for spin form geometry...')
    return {'validated': True}

graph = StateGraph(SpinFormState)
graph.add_node('validate', validate_specs)
graph.add_node('manufacture', process_manufacturing)
graph.set_entry_point('validate')
graph.add_edge('validate', 'manufacture')
graph.add_edge('manufacture', END)
graph = graph.compile()
