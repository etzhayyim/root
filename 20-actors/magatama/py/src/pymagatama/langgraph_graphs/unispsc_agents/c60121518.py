from typing import TypedDict
from langgraph.graph import StateGraph, END

class PencilSpecState(TypedDict):
    hardness: str
    is_non_toxic: bool
    passed_qc: bool

def validate_hardness(state: PencilSpecState):
    valid_grades = ['HB', '2B', '4B', 'H', '2H']
    return {'passed_qc': state['hardness'] in valid_grades}

def check_safety(state: PencilSpecState):
    return {'passed_qc': state['passed_qc'] and state['is_non_toxic']}

graph = StateGraph(PencilSpecState)
graph.add_node('validate', validate_hardness)
graph.add_node('safety', check_safety)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()
