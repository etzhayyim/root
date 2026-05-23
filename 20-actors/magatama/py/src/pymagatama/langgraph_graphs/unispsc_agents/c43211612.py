from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class KitState(TypedDict):
    items: List[str]
    validated: bool

def validate_components(state: KitState):
    required = {'mouse', 'keyboard', 'cable'}
    state['validated'] = all(item in state['items'] for item in required)
    return state

def package_order(state: KitState):
    return {'status': 'ready_to_ship' if state['validated'] else 'incomplete'}

graph = StateGraph(KitState)
graph.add_node('validate', validate_components)
graph.add_node('package', package_order)
graph.add_edge('validate', 'package')
graph.add_edge('package', END)
graph.set_entry_point('validate')
graph = graph.compile()
