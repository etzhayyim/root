from langgraph.graph import StateGraph, END
from typing import TypedDict
class DegausserState(TypedDict):
    model_number: str
    field_strength: int
    is_compliant: bool

def validate_specs(state: DegausserState):
    state['is_compliant'] = state['field_strength'] >= 10000
    return state

def check_certification(state: DegausserState):
    print(f'Checking compliance for {state['model_number']}')
    return state

graph = StateGraph(DegausserState)
graph.add_node('validate', validate_specs)
graph.add_node('certify', check_certification)
graph.set_entry_point('validate')
graph.add_edge('validate', 'certify')
graph.add_edge('certify', END)
graph = graph.compile()
