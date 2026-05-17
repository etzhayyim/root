from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class BindingSpecState(TypedDict):
    spine_diameter: float
    material: str
    is_compliant: bool

def validate_spec(state: BindingSpecState):
    state['is_compliant'] = state['spine_diameter'] > 0 and state['material'] in ['PVC', 'Metal', 'PP']
    return state

def check_compat(state: BindingSpecState):
    print(f'Checking compatibility for {state['material']} spine')
    return {'is_compliant': state['is_compliant']}

graph = StateGraph(BindingSpecState)
graph.add_node('validate', validate_spec)
graph.add_node('compatibility', check_compat)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compatibility')
graph.add_edge('compatibility', END)
graph = graph.compile()