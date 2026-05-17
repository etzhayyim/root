from typing import TypedDict
from langgraph.graph import StateGraph, END

class StereoSpecState(TypedDict):
    model_name: str
    power_rating: float
    compliant: bool

def validate_specs(state: StereoSpecState):
    # Business logic for home stereo validation
    if state['power_rating'] > 0:
        state['compliant'] = True
    return state

def determine_certification(state: StereoSpecState):
    print(f'Checking compliance for {state['model_name']}')
    return 'end_node'

graph = StateGraph(StereoSpecState)
graph.add_node('validate', validate_specs)
graph.add_node('certify', determine_certification)
graph.add_edge('validate', 'certify')
graph.add_edge('certify', END)
graph.set_entry_point('validate')
graph = graph.compile()