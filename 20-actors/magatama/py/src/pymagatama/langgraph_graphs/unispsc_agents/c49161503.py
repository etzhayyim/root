from typing import TypedDict
from langgraph.graph import StateGraph, END

class BaseballState(TypedDict):
    specs: dict
    approved: bool

def validate_specs(state: BaseballState):
    s = state['specs']
    valid = (142 <= s.get('weight', 0) <= 149) and (s.get('seam') == 'raised')
    return {'approved': valid}

graph = StateGraph(BaseballState)
graph.add_node('validation', validate_specs)
graph.set_entry_point('validation')
graph.add_edge('validation', END)
graph = graph.compile()
