from typing import TypedDict
from langgraph.graph import StateGraph, END

class TankProcurementState(TypedDict):
    tank_capacity: float
    material_spec: str
    is_compliant: bool

def validate_specifications(state: TankProcurementState):
    state['is_compliant'] = state['tank_capacity'] > 0 and state['material_spec'] != ''
    return state

def check_safety_protocols(state: TankProcurementState):
    if state['is_compliant']:
        print('Safety protocol check passed.')
    return state

graph = StateGraph(TankProcurementState)
graph.add_node('validate', validate_specifications)
graph.add_node('safety', check_safety_protocols)
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph.set_entry_point('validate')
app = graph.compile()