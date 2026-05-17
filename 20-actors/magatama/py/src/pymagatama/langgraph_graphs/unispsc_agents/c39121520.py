from typing import TypedDict
from langgraph.graph import StateGraph, END

class RelayState(TypedDict):
    specs: dict
    validated: bool
    error: str

def validate_specs(state: RelayState):
    required = ['rated_current_range', 'trip_class']
    if all(k in state['specs'] for k in required):
        return {'validated': True}
    return {'validated': False, 'error': 'Missing required technical specifications'}

def decision_node(state: RelayState):
    return 'process' if state['validated'] else END

graph = StateGraph(RelayState)
graph.add_node('validate', validate_specs)
graph.add_node('process', lambda s: {'error': 'Proceeding to manufacturing validation'})
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')
graph = graph.compile()