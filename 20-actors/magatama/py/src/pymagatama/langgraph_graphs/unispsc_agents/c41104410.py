from typing import TypedDict
from langgraph.graph import StateGraph, END

class IncubatorState(TypedDict):
    temp_celsius: float
    co2_percent: float
    humidity_percent: float
    status: str

def validate_specs(state: IncubatorState):
    if state['temp_celsius'] > 45 or state['temp_celsius'] < 30:
        return {'status': 'Invalid temperature range'}
    return {'status': 'Validated'}

def process_deployment(state: IncubatorState):
    return {'status': 'Ready for installation'}

graph = StateGraph(IncubatorState)
graph.add_node('validate', validate_specs)
graph.add_node('deploy', process_deployment)
graph.add_edge('validate', 'deploy')
graph.add_edge('deploy', END)
graph.set_entry_point('validate')
graph = graph.compile()
