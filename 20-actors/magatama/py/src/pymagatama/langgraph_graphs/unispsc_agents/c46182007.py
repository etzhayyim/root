from typing import TypedDict
from langgraph.graph import StateGraph, END

class PAPRState(TypedDict):
    model_number: str
    certification_valid: bool
    airflow_check: bool
    status: str

def validate_certification(state: PAPRState):
    state['certification_valid'] = True if state.get('model_number') else False
    return 'check_airflow'

def check_airflow(state: PAPRState):
    state['airflow_check'] = True
    state['status'] = 'COMPLIANT' if state['certification_valid'] else 'REJECTED'
    return END

graph = StateGraph(PAPRState)
graph.add_node('validate_cert', validate_certification)
graph.add_node('check_airflow', check_airflow)
graph.set_entry_point('validate_cert')
graph.add_edge('validate_cert', 'check_airflow')
graph.add_edge('check_airflow', END)
graph = graph.compile()