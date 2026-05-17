from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class KeyboardState(TypedDict):
    input_data: str
    validation_log: Annotated[list, add_messages]
    is_compliant: bool

def validate_layout(state: KeyboardState):
    log = f'Validating layout for: {state.input_data}'
    return {'validation_log': [log], 'is_compliant': True}

def process_input(state: KeyboardState):
    return {'validation_log': ['Input processing complete']}

graph = StateGraph(KeyboardState)
graph.add_node('validate', validate_layout)
graph.add_node('process', process_input)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph = graph.compile()