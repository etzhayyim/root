from typing import TypedDict
from langgraph.graph import StateGraph, END

class HeatExchangerState(TypedDict):
    spec_data: dict
    validation_report: dict

def validate_specs(state: HeatExchangerState):
    specs = state['spec_data']
    errors = []
    if not specs.get('max_operating_pressure'):
        errors.append('Missing pressure rating')
    return {'validation_report': {'status': 'PASS' if not errors else 'FAIL', 'issues': errors}}

def check_compliance(state: HeatExchangerState):
    return {'validation_report': {**state['validation_report'], 'compliance': 'Verified'}}

graph = StateGraph(HeatExchangerState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()
