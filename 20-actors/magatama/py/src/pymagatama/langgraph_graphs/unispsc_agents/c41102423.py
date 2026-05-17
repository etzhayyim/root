from typing import TypedDict
from langgraph.graph import StateGraph, END

class HotplateState(TypedDict):
    specs: dict
    validation_passed: bool
graph = StateGraph(HotplateState)
def validate_specs(state: HotplateState):
    state['validation_passed'] = all(k in state['specs'] for k in ['temp', 'rpm'])
    print('Validating stirring hotplate specifications...')
    return 'passed' if state['validation_passed'] else 'failed'
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
compiled_graph = graph.compile()