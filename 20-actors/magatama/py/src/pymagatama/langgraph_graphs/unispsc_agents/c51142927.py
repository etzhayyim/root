from typing import TypedDict
from langgraph.graph import StateGraph, END

class DesfluraneState(TypedDict):
    concentration: float
    batch_id: str
    is_compliant: bool

def validate_batch(state: DesfluraneState):
    state['is_compliant'] = (state['concentration'] >= 99.0) and (len(state['batch_id']) > 5)
    return state

def check_regulations(state: DesfluraneState):
    print(f'Checking compliance for {state['batch_id']}')
    return state

graph = StateGraph(DesfluraneState)
graph.add_node('validate', validate_batch)
graph.add_node('compliance', check_regulations)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph.compile()
