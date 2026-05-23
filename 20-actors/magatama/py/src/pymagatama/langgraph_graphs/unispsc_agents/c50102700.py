from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class FrozenBerryState(TypedDict):
    batch_id: str
    temperature_logs: List[float]
    passed_inspection: bool

def validate_cold_chain(state: FrozenBerryState):
    temp_avg = sum(state['temperature_logs']) / len(state['temperature_logs'])
    return {'passed_inspection': temp_avg <= -18.0}

def update_inventory(state: FrozenBerryState):
    print(f'Batch {state['batch_id']} cleared for warehouse storage.')
    return {}

builder = StateGraph(FrozenBerryState)
builder.add_node('validate_cold_chain', validate_cold_chain)
builder.add_node('update_inventory', update_inventory)
builder.add_edge('validate_cold_chain', 'update_inventory')
builder.set_entry_point('validate_cold_chain')
builder.add_edge('update_inventory', END)
graph = builder.compile()
