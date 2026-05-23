from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class TractorState(TypedDict):
    tractor_id: str
    specs: dict
    approved: bool

def validate_specs(state: TractorState):
    # Simulate CAD/Spec validation logic
    hp = state['specs'].get('hp', 0)
    state['approved'] = hp > 50
    return state

def workflow_node(state: TractorState):
    print(f'Processing tractor {state['tractor_id']}')
    return state

graph = StateGraph(TractorState)
graph.add_node('validate', validate_specs)
graph.add_node('process', workflow_node)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph = graph.compile()
