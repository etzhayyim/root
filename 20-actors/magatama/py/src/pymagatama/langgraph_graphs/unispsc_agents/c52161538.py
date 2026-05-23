from typing import TypedDict
from langgraph.graph import StateGraph, END

class TapeRewinderState(TypedDict):
    tape_format: str
    rewind_speed: str
    is_verified: bool

def validate_specs(state: TapeRewinderState):
    state['is_verified'] = state['tape_format'] in ['VHS', 'Betacam', 'U-matic']
    return state

def process_procurement(state: TapeRewinderState):
    return {'is_verified': True}

graph = StateGraph(TapeRewinderState)
graph.add_node('validate', validate_specs)
graph.add_node('process', process_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph = graph.compile()
