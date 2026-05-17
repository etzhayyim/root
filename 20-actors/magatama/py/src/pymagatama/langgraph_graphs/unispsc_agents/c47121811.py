from typing import TypedDict
from langgraph.graph import StateGraph, END

class DuctCleanState(TypedDict):
    spec_sheet: dict
    validation_results: list

def validate_airflow(state: DuctCleanState):
    cfm = state['spec_sheet'].get('cfm', 0)
    if cfm < 500: return {'validation_results': ['Airflow insufficient']}
    return {'validation_results': ['Airflow validated']}

def inspect_filters(state: DuctCleanState):
    if state['spec_sheet'].get('hepa_grade') != 'H13':
        return {'validation_results': state['validation_results'] + ['Filter insufficient']}
    return {'validation_results': state['validation_results'] + ['Filter compliant']}

graph = StateGraph(DuctCleanState)
graph.add_node('validate_airflow', validate_airflow)
graph.add_node('inspect_filters', inspect_filters)
graph.set_entry_point('validate_airflow')
graph.add_edge('validate_airflow', 'inspect_filters')
graph.add_edge('inspect_filters', END)
graph = graph.compile()