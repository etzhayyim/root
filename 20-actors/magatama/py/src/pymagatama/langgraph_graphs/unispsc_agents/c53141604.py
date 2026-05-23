from typing import TypedDict
from langgraph.graph import StateGraph, END

class SewingPatternState(TypedDict):
    pattern_id: str
    format: str
    is_valid: bool

def validate_pattern(state: SewingPatternState):
    print(f'Validating pattern {state['pattern_id']}...')
    state['is_valid'] = True
    return state

def process_delivery(state: SewingPatternState):
    print(f'Processing delivery for {state['format']}...')
    return {'is_valid': True}

graph = StateGraph(SewingPatternState)
graph.add_node('validate', validate_pattern)
graph.add_node('delivery', process_delivery)
graph.set_entry_point('validate')
graph.add_edge('validate', 'delivery')
graph.add_edge('delivery', END)
app = graph.compile()
