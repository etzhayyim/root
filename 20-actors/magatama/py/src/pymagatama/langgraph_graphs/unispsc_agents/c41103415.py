from typing import TypedDict
from langgraph.graph import StateGraph, END

class CleanBenchState(TypedDict):
    iso_class: str
    filter_integrity: bool
    airflow_velocity: float

def validate_specs(state: CleanBenchState):
    if state['iso_class'] not in ['ISO 5', 'ISO 7']:
        raise ValueError('Invalid clean room standard')
    return {'filter_integrity': True}

def certify_performance(state: CleanBenchState):
    print('Verifying HEPA filter certifications...')
    return {'airflow_velocity': 0.45}

graph = StateGraph(CleanBenchState)
graph.add_node('validate', validate_specs)
graph.add_node('certify', certify_performance)
graph.add_edge('validate', 'certify')
graph.add_edge('certify', END)
graph.set_entry_point('validate')
graph = graph.compile()