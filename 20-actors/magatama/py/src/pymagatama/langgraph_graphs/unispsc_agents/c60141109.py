from typing import TypedDict
from langgraph.graph import StateGraph, END

class GameState(TypedDict):
    game_title: str
    participant_count: int
    is_compliant: bool

def validate_game_specs(state: GameState) -> GameState:
    if state['participant_count'] < 2:
        state['is_compliant'] = False
    else:
        state['is_compliant'] = True
    return state

def finalize_procurement(state: GameState) -> GameState:
    return state

graph_builder = StateGraph(GameState)
graph_builder.add_node('validate', validate_game_specs)
graph_builder.add_node('finalize', finalize_procurement)
graph_builder.set_entry_point('validate')
graph_builder.add_edge('validate', 'finalize')
graph_builder.add_edge('finalize', END)
graph = graph_builder.compile()
