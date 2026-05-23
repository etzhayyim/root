from typing import TypedDict
from langgraph.graph import StateGraph, END

class IrrigatorState(TypedDict):
    load_capacity_kg: float
    material_compliance: bool
    is_approved: bool

def validate_load_capacity(state: IrrigatorState):
    state['is_approved'] = True if state['load_capacity_kg'] >= 5.0 else False
    return state

def check_compliance(state: IrrigatorState):
    state['is_approved'] = state['is_approved'] and state['material_compliance']
    return state

graph = StateGraph(IrrigatorState)
graph.add_node('validate', validate_load_capacity)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
