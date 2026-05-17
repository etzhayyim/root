from typing import TypedDict
from langgraph.graph import StateGraph, END

class WorkflowState(TypedDict):
    spec_data: dict
    validation_log: list
    is_compliant: bool

def validate_airflow(state: WorkflowState):
    velocity = state['spec_data'].get('airflow_velocity_m_per_s', 0)
    valid = 0.3 <= velocity <= 0.5
    return {'is_compliant': valid, 'validation_log': ['Airflow check: ' + str(valid)]}

def check_hepa(state: WorkflowState):
    eff = state['spec_data'].get('HEPA_filter_efficiency', 0)
    return {'is_compliant': state['is_compliant'] and (eff >= 99.97)}

graph = StateGraph(WorkflowState)
graph.add_node('validate_airflow', validate_airflow)
graph.add_node('check_hepa', check_hepa)
graph.set_entry_point('validate_airflow')
graph.add_edge('validate_airflow', 'check_hepa')
graph.add_edge('check_hepa', END)
graph = graph.compile()