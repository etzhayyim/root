from typing import TypedDict
from langgraph.graph import StateGraph, END

class PowerControlState(TypedDict):
    spec_data: dict
    validation_results: list
    is_compliant: bool

def validate_specs(state: PowerControlState):
    specs = state['spec_data']
    results = []
    if 'rated_voltage' not in specs: results.append('Missing voltage spec')
    if 'communication_protocols' not in specs: results.append('No protocols specified')
    return {'validation_results': results, 'is_compliant': len(results) == 0}

def route_by_compliance(state: PowerControlState):
    return 'compliant' if state['is_compliant'] else 'manual_review'

graph = StateGraph(PowerControlState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')