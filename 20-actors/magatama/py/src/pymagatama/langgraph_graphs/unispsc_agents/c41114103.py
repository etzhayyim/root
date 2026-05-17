from typing import TypedDict
from langgraph.graph import StateGraph, END

class SeismicState(TypedDict):
    sensitivity: float
    status: str
    validation_score: float

def validate_sensor(state: SeismicState):
    score = 1.0 if state['sensitivity'] > 0.5 else 0.5
    return {'validation_score': score, 'status': 'VALIDATED'}

def deploy_module(state: SeismicState):
    return {'status': 'DEPLOYED'}

graph = StateGraph(SeismicState)
graph.add_node('validate', validate_sensor)
graph.add_node('deploy', deploy_module)
graph.set_entry_point('validate')
graph.add_edge('validate', 'deploy')
graph.add_edge('deploy', END)
graph = graph.compile()