from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class DesiccatorState(TypedDict):
    pressure_limit: float
    material_certified: bool
    validation_passed: bool

def validate_specs(state: DesiccatorState):
    state['validation_passed'] = state['pressure_limit'] >= 1000 and state['material_certified']
    return 'validate_specs'

def finalize_order(state: DesiccatorState):
    return 'order_finalized'

graph = StateGraph(DesiccatorState)
graph.add_node('validate', validate_specs)
graph.add_node('finalize', finalize_order)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()