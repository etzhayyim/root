from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PlayState(TypedDict):
    specs: dict
    validated: bool
    errors: List[str]

def validate_safety(state: PlayState):
    errors = []
    if 'safety_cert' not in state['specs']: errors.append('Missing safety cert')
    return {'validated': len(errors) == 0, 'errors': errors}

def assembly_check(state: PlayState):
    return {'errors': state['errors'] + ['Check assembly complexity']}

graph = StateGraph(PlayState)
graph.add_node('safety', validate_safety)
graph.add_node('assembly', assembly_check)
graph.set_entry_point('safety')
graph.add_edge('safety', 'assembly')
graph.add_edge('assembly', END)
graph = graph.compile()