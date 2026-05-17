from typing import TypedDict
from langgraph.graph import StateGraph, END

class AssemblyState(TypedDict):
    part_id: str
    weld_integrity: bool
    pressure_test_passed: bool

def validate_weld(state: AssemblyState) -> AssemblyState:
    print(f'Validating ultrasonic weld for {state[\'part_id\']}')
    state['weld_integrity'] = True
    return state

def run_pressure_test(state: AssemblyState) -> AssemblyState:
    print(f'Running pneumatic pressure test on {state[\'part_id\']}')
    state['pressure_test_passed'] = True
    return state

builder = StateGraph(AssemblyState)
builder.add_node('weld_check', validate_weld)
builder.add_node('pressure_test', run_pressure_test)
builder.add_edge('weld_check', 'pressure_test')
builder.add_edge('pressure_test', END)
builder.set_entry_point('weld_check')
graph = builder.compile()