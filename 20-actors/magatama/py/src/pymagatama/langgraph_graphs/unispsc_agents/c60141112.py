from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class GameBookState(TypedDict):
    book_titles: List[str]
    validated_titles: List[str]
    requires_review: bool

def validate_titles(state: GameBookState):
    validated = [title for title in state['book_titles'] if len(title) > 0]
    return {'validated_titles': validated, 'requires_review': False}

def check_compliance(state: GameBookState):
    return {'requires_review': any('Restricted' in t for t in state['validated_titles'])}

graph = StateGraph(GameBookState)
graph.add_node('validate', validate_titles)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()