from typing import TypedDict
from langgraph.graph import StateGraph, END

class ColumnState(TypedDict):
    specs: dict
    approved: bool

def validate_load_capacity(state: ColumnState):
    capacity = state['specs'].get('load_capacity', 0)
    return {'approved': capacity > 0}

def structural_check(state: ColumnState):
    print(f'Checking structural integrity for: {state["specs"]}')
    return {'approved': True}

graph = StateGraph(ColumnState)
graph.add_node('validate', validate_load_capacity)
graph.add_node('structural', structural_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'structural')
graph.add_edge('structural', END)
graph = graph.compile()
