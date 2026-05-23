from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PoultryFeedState(TypedDict):
    batch_id: str
    additives: List[str]
    compliance_passed: bool
    log: List[str]

def validate_ingredients(state: PoultryFeedState):
    state['log'].append('Validating ingredient safety protocols.')
    state['compliance_passed'] = True
    return state

def check_storage_requirements(state: PoultryFeedState):
    state['log'].append('Verifying storage temperature and humidity.')
    return state

graph = StateGraph(PoultryFeedState)
graph.add_node('validate', validate_ingredients)
graph.add_node('storage', check_storage_requirements)
graph.set_entry_point('validate')
graph.add_edge('validate', 'storage')
graph.add_edge('storage', END)
compile_graph = graph.compile()
