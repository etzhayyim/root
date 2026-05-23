from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class MineralDrillingState(TypedDict):
    material_id: str
    viscosity_requirements: float
    safety_clearance: bool
    process_logs: Annotated[Sequence[str], operator.add]

def validate_safety_protocols(state: MineralDrillingState) -> MineralDrillingState:
    # Logic for checking dangerous goods compliance
    state['safety_clearance'] = True
    return {'process_logs': ['Safety protocols validated for drilling chemical']}

def simulate_drilling_fluid_performance(state: MineralDrillingState) -> MineralDrillingState:
    # Logic for testing performance under pressure
    return {'process_logs': ['Performance simulation completed for viscosity: ' + str(state['viscosity_requirements'])]}

builder = StateGraph(MineralDrillingState)
builder.add_node('safety_check', validate_safety_protocols)
builder.add_node('perf_sim', simulate_drilling_fluid_performance)
builder.set_entry_point('safety_check')
builder.add_edge('safety_check', 'perf_sim')
builder.add_edge('perf_sim', END)
graph = builder.compile()
