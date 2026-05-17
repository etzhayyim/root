from typing import TypedDict
from langgraph.graph import StateGraph, END
class EnclosureState(TypedDict):
    airflow_velocity: float
    filter_saturation_level: float
    validation_passed: bool
def check_airflow(state: EnclosureState):
    state['validation_passed'] = state['airflow_velocity'] > 0.5
    return state
def evaluate_safety(state: EnclosureState):
    if state['filter_saturation_level'] > 0.8: print('Warning: Filter replacement required')
    return state
graph = StateGraph(EnclosureState)
graph.add_node('validate_airflow', check_airflow)
graph.add_node('safety_check', evaluate_safety)
graph.set_entry_point('validate_airflow')
graph.add_edge('validate_airflow', 'safety_check')
graph.add_edge('safety_check', END)
compile_graph = graph.compile()