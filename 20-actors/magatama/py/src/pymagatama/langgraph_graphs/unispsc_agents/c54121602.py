from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class JadeState(TypedDict):
    cert_provided: bool
    hardness: float
    origin: str
    approved: bool

def validate_gemstone(state: JadeState):
    if state['cert_provided'] and state['hardness'] >= 6.0:
        return {'approved': True}
    return {'approved': False}

graph = StateGraph(JadeState)
graph.add_node('validation', validate_gemstone)
graph.set_entry_point('validation')
graph.add_edge('validation', END)
graph = graph.compile()
