from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class PaperState(TypedDict):
    gsm: int
    brightness: int
    verified: bool
    history: List[str]

def validate_gsm(state: PaperState) -> PaperState:
    if 60 <= state['gsm'] <= 120:
        state['history'].append('GSM validated')
    else:
        state['verified'] = False
    return state

def check_brightness(state: PaperState) -> PaperState:
    if state['brightness'] >= 85:
        state['history'].append('Brightness validated')
        state['verified'] = True
    else:
        state['verified'] = False
    return state

graph = StateGraph(PaperState)
graph.add_node('validate_gsm', validate_gsm)
graph.add_node('check_brightness', check_brightness)
graph.set_entry_point('validate_gsm')
graph.add_edge('validate_gsm', 'check_brightness')
graph.add_edge('check_brightness', END)
app = graph.compile()
