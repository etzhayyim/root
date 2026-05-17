from typing import TypedDict
from langgraph.graph import StateGraph, END

class ToolSpecState(TypedDict):
    material: str
    hardness: int
    is_compliant: bool

def validate_spec(state: ToolSpecState):
    if state['hardness'] >= 50:
        return {'is_compliant': True}
    return {'is_compliant': False}

def process_procurement(state: ToolSpecState):
    print('Procurement processing for nut driver bits initiated.')
    return state

graph = StateGraph(ToolSpecState)
graph.add_node('validate', validate_spec)
graph.add_node('process', process_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph = graph.compile()