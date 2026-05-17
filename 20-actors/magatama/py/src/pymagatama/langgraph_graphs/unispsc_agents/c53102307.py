from typing import TypedDict
from langgraph.graph import StateGraph, END

class GarmentState(TypedDict):
    specifications: dict
    is_compliant: bool

def validate_materials(state: GarmentState):
    specs = state.get('specifications', {})
    compliant = 'elasticity_retention' in specs and 'oeko_tex' in specs
    return {'is_compliant': compliant}

def route_by_compliance(state: GarmentState):
    if state['is_compliant']:
        return 'final'
    return 'flag_for_review'

graph = StateGraph(GarmentState)
graph.add_node('validate', validate_materials)
graph.add_edge('validate', 'final')
graph.set_entry_point('validate')
graph.add_edge('validate', END)
compiled_graph = graph.compile()