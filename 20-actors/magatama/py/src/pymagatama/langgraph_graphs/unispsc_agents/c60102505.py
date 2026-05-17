from typing import TypedDict
from langgraph.graph import StateGraph, END

class TextbookState(TypedDict):
    title: str
    grade_level: str
    is_validated: bool

def validate_content(state: TextbookState):
    print(f'Validating content for {state[\'title\']}')
    return {'is_validated': True}

def format_for_school(state: TextbookState):
    print('Formatting print specification')
    return {'is_validated': True}

graph = StateGraph(TextbookState)
graph.add_node('validate', validate_content)
graph.add_node('format', format_for_school)
graph.set_entry_point('validate')
graph.add_edge('validate', 'format')
graph.add_edge('format', END)
graph = graph.compile()