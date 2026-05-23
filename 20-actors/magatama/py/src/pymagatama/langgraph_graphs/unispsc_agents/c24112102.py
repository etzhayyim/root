from typing import TypedDict
from langgraph.graph import StateGraph, END

class BarrelProcurementState(TypedDict):
    capacity: float
    material: str
    un_certified: bool
    validation_passed: bool

def validate_specs(state: BarrelProcurementState):
    state['validation_passed'] = bool(state['material'] and state['capacity'] > 0)
    return state

def check_compliance(state: BarrelProcurementState):
    if state['un_certified'] and state['material'] == 'steel':
        print('High compliance path identified.')
    return {'validation_passed': True}

graph = StateGraph(BarrelProcurementState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
app = graph.compile()
