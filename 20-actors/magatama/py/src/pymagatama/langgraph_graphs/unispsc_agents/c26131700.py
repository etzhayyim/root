from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class MonitoringState(TypedDict):
    device_specs: dict
    validation_logs: List[str]
    is_compliant: bool

def validate_specs(state: MonitoringState):
    specs = state['device_specs']
    logs = []
    compliant = True
    if specs.get('voltage', 0) > 1000: logs.append('Voltage exceeds safety threshold')
    if not specs.get('protocol'): 
        logs.append('Protocol missing'); compliant = False
    return {'validation_logs': logs, 'is_compliant': compliant}

def route_by_compliance(state: MonitoringState):
    return 'compliant_path' if state['is_compliant'] else 'manual_review'

graph = StateGraph(MonitoringState)
graph.add_node('validate', validate_specs)
graph.add_conditional_edges('validate', route_by_compliance, {'compliant_path': END, 'manual_review': END})
graph.set_entry_point('validate')
app = graph.compile()