from typing import TypedDict
from langgraph.graph import StateGraph, END

class BallQualityState(TypedDict):
    diameter: float
    weight: float
    ittf_certified: bool
    passed: bool

def validate_ball_specs(state: BallQualityState):
    # ITTF standard: 40mm diameter and 2.7g weight
    is_compliant = (39.5 <= state['diameter'] <= 40.5) and (2.6 <= state['weight'] <= 2.8) and state['ittf_certified']
    return {'passed': is_compliant}

graph = StateGraph(BallQualityState)
graph.add_node('validate', validate_ball_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()