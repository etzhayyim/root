from typing import TypedDict
from langgraph.graph import StateGraph, END

class SolarArrayState(TypedDict):
    spec: dict
    validation_passed: bool
    compliance_risk: str

def validate_efficiency(state: SolarArrayState):
    efficiency = state['spec'].get('efficiency', 0)
    return {'validation_passed': efficiency > 0.30}

def check_compliance(state: SolarArrayState):
    return {'compliance_risk': 'ITAR_REQUIRED'}

graph = StateGraph(SolarArrayState)
graph.add_node('validate', validate_efficiency)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
app = graph.compile()
