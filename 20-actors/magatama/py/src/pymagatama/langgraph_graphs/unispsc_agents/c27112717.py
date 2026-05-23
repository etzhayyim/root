from langgraph.graph import StateGraph, END
from typing import TypedDict
class HeatGunState(TypedDict):
    temp_setting: float
    airflow: float
    has_safety_cert: bool
def validate_specs(state: HeatGunState):
    if state['temp_setting'] > 650: return 'overheat_risk'
    return 'safe'
def check_safety_standards(state: HeatGunState):
    return {'is_compliant': state['has_safety_cert']}
graph = StateGraph(HeatGunState)
graph.add_node('validate', validate_specs)
graph.add_node('safety_check', check_safety_standards)
graph.add_edge('validate', 'safety_check')
graph.add_edge('safety_check', END)
graph.set_entry_point('validate')
graph = graph.compile()
