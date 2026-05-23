from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class MicroSyringeState(TypedDict):
    specs: dict
    validation_passed: bool
    errors: List[str]

def validate_specs(state: MicroSyringeState):
    required = ['volume', 'gauge', 'sterility']
    errors = [f'Missing {f}' for f in required if f not in state['specs']]
    return {'validation_passed': len(errors) == 0, 'errors': errors}

def check_regulatory(state: MicroSyringeState):
    print('Performing regulatory screening for medical device...')
    return {'validation_passed': state['validation_passed']}

graph = StateGraph(MicroSyringeState)
graph.add_node('validate', validate_specs)
graph.add_node('regulatory', check_regulatory)
graph.set_entry_point('validate')
graph.add_edge('validate', 'regulatory')
graph.add_edge('regulatory', END)
graph = graph.compile()
