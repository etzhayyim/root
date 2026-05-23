from langgraph.graph import StateGraph, END
from typing import TypedDict
class TapeState(TypedDict):
    tape_type: str
    capacity: str
    validated: bool
def validate_tape_spec(state: TapeState):
    state['validated'] = state['tape_type'] in ['LTO-9', 'LTO-8'] and int(state['capacity'].replace('TB', '')) > 0
    return state
graph = StateGraph(TapeState)
graph.add_node('validate', validate_tape_spec)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
