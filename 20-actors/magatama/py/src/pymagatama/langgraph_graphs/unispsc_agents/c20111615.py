from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class PumpState(TypedDict):
    pressure_target: float
    flow_rate: float
    validation_passed: bool
    log: list[str]

def validate_pump_specs(state: PumpState) -> PumpState:
    if state['pressure_target'] > 35.0:
        state['log'].append('Critical: Pressure exceeds safety rating')
        state['validation_passed'] = False
    else:
        state['validation_passed'] = True
    return state

def assemble_pump_logic(state: PumpState) -> PumpState:
    state['log'].append('Assembling hydraulic piston pump module')
    return state

graph = StateGraph(PumpState)
graph.add_node('validate', validate_pump_specs)
graph.add_node('assemble', assemble_pump_logic)
graph.set_entry_point('validate')
graph.add_edge('validate', 'assemble')
graph.add_edge('assemble', END)
graph = graph.compile()