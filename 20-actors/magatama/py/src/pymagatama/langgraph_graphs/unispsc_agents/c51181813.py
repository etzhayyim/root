from typing import TypedDict
from langgraph.graph import StateGraph, END

class EstradiolState(TypedDict):
    batch_number: str
    purity_level: float
    compliant: bool

def validate_purity(state: EstradiolState) -> EstradiolState:
    state['compliant'] = state['purity_level'] >= 99.0
    return state

def check_compliance(state: EstradiolState) -> str:
    return 'END' if state['compliant'] else 'END'

graph = StateGraph(EstradiolState)
graph.add_node('validate', validate_purity)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()