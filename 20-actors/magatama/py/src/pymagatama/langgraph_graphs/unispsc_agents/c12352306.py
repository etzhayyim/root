from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class AdhesiveState(TypedDict):
    spec_data: dict
    validation_results: list
    ready_for_procurement: bool

def validate_chemistry(state: AdhesiveState) -> AdhesiveState:
    # Logic to check chemical compliance against industry standards
    state['validation_results'].append('Chemistry Validated')
    return state

def check_durability(state: AdhesiveState) -> AdhesiveState:
    # Perform simulated stress testing validation
    state['validation_results'].append('Durability Verified')
    state['ready_for_procurement'] = True
    return state

graph = StateGraph(AdhesiveState)
graph.add_node('validate', validate_chemistry)
graph.add_node('stress_test', check_durability)
graph.add_edge('validate', 'stress_test')
graph.add_edge('stress_test', END)
graph.set_entry_point('validate')
graph = graph.compile()