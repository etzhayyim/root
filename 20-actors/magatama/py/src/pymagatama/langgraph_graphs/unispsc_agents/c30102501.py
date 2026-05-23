from typing import TypedDict
from langgraph.graph import StateGraph, END

class AlloyState(TypedDict):
    material_specs: dict
    approved: bool

def validate_alloy_specs(state: AlloyState):
    specs = state.get('material_specs', {})
    is_compliant = specs.get('tensile_strength', 0) > 400 and 'mill_cert' in specs
    return {'approved': is_compliant}

def route_by_compliance(state: AlloyState):
    return 'process' if state['approved'] else END

graph = StateGraph(AlloyState)
graph.add_node('validate', validate_alloy_specs)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_compliance, {'process': END})
graph.add_edge('validate', END)
graph = graph.compile()
