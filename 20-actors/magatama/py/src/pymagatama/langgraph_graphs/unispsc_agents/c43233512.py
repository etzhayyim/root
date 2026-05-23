from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class RingtoneState(TypedDict):
    software_id: str
    file_format: str
    is_licensed: bool
    validation_passed: bool

def validate_format(state: RingtoneState):
    state['validation_passed'] = state['file_format'] in ['mp3', 'm4r', 'wav']
    return state

def check_license(state: RingtoneState):
    state['is_licensed'] = True
    return state

graph = StateGraph(RingtoneState)
graph.add_node('validate', validate_format)
graph.add_node('license', check_license)
graph.set_entry_point('validate')
graph.add_edge('validate', 'license')
graph.add_edge('license', END)
app = graph.compile()
