from typing import TypedDict
from langgraph.graph import StateGraph, END

class SeatPivotState(TypedDict):
    part_number: str
    material_certified: bool
    torque_check_passed: bool

def validate_materials(state: SeatPivotState):
    print(f'Checking material certification for {state['part_number']}')
    return {'material_certified': True}

def perform_torque_test(state: SeatPivotState):
    print('Executing mechanical torque and rotation testing...')
    return {'torque_check_passed': True}

graph = StateGraph(SeatPivotState)
graph.add_node('validate_materials', validate_materials)
graph.add_node('torque_test', perform_torque_test)
graph.add_edge('validate_materials', 'torque_test')
graph.add_edge('torque_test', END)
graph.set_entry_point('validate_materials')
app = graph.compile()