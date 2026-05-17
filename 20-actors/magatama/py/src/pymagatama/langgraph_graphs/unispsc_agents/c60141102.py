from typing import TypedDict
from langgraph.graph import StateGraph, END

class GameState(TypedDict):
    game_specs: dict
    compliance_passed: bool

def validate_components(state: GameState):
    required = ['board', 'pieces', 'instructions']
    passed = all(k in state['game_specs'].get('components', []) for k in required)
    return {'compliance_passed': passed}

def check_certification(state: GameState):
    cert = state['game_specs'].get('certifications', [])
    return {'compliance_passed': 'EN71' in cert}

graph = StateGraph(GameState)
graph.add_node('validate', validate_components)
graph.add_node('certify', check_certification)
graph.set_entry_point('validate')
graph.add_edge('validate', 'certify')
graph.add_edge('certify', END)
graph = graph.compile()