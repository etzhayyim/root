from typing import TypedDict
from langgraph.graph import StateGraph, END

class MattressVentilatorState(TypedDict):
    specs: dict
    validation_results: list
    is_compliant: bool

def validate_specs(state: MattressVentilatorState):
    required = ['Airflow Capacity', 'Noise Level', 'Power Consumption']
    compliance = all(k in state['specs'] for k in required)
    return {'validation_results': ['Compliance Check Passed' if compliance else 'Missing Data'], 'is_compliant': compliance}

def safety_check(state: MattressVentilatorState):
    return {'validation_results': state['validation_results'] + ['Safety Inspection Scheduled']}

graph = StateGraph(MattressVentilatorState)
graph.add_node('validation', validate_specs)
graph.add_node('safety', safety_check)
graph.set_entry_point('validation')
graph.add_edge('validation', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()
