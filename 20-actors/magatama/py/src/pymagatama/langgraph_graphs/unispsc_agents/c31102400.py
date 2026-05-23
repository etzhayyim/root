from typing import TypedDict
from langgraph.graph import StateGraph, END

class VProcessState(TypedDict):
    spec_data: dict
    validation_passed: bool

def validate_vprocess_spec(state: VProcessState):
    # Perform specific checks for casting tolerances and metallurgy
    print('Validating V-Process dimensional and material standards...')
    state['validation_passed'] = 'tolerance' in state['spec_data'] and 'material' in state['spec_data']
    return state

graph = StateGraph(VProcessState)
graph.add_node('validate', validate_vprocess_spec)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
