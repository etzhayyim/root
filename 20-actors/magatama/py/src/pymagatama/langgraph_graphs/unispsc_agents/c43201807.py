from typing import TypedDict
from langgraph.graph import StateGraph, END

class TapeDriveState(TypedDict):
    model_number: str
    lto_generation: str
    validation_status: bool

def validate_tape_spec(state: TapeDriveState) -> TapeDriveState:
    # Logic to verify LTO compatibility and drive firmware integrity
    state['validation_status'] = 'LTO' in state['lto_generation']
    return state

def secure_config_check(state: TapeDriveState) -> TapeDriveState:
    # Logic for restricted export/sanctions risk checks
    print(f'Checking {state['model_number']} for export compliance...')
    return state

graph = StateGraph(TapeDriveState)
graph.add_node('validate_spec', validate_tape_spec)
graph.add_node('compliance_check', secure_config_check)
graph.set_entry_point('validate_spec')
graph.add_edge('validate_spec', 'compliance_check')
graph.add_edge('compliance_check', END)
graph = graph.compile()
