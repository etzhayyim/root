from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class PulpState(TypedDict):
    pulp_id: str
    brightness: float
    freeness: float
    status: str

def validate_brightness(state: PulpState):
    if state['brightness'] < 80.0:
        return {'status': 'rejected_low_brightness'}
    return {'status': 'brightness_validated'}

def validate_freeness(state: PulpState):
    if state['freeness'] < 400.0:
        return {'status': 'rejected_low_freeness'}
    return {'status': 'freeness_validated'}

graph = StateGraph(PulpState)
graph.add_node('check_brightness', validate_brightness)
graph.add_node('check_freeness', validate_freeness)
graph.set_entry_point('check_brightness')
graph.add_edge('check_brightness', 'check_freeness')
graph.add_edge('check_freeness', END)

compiled_graph = graph.compile()