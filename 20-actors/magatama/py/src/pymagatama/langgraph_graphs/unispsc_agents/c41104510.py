from typing import TypedDict
from langgraph.graph import StateGraph, END

class DryingOvenState(TypedDict):
    specs: dict
    validation_passed: bool

def validate_specs(state: DryingOvenState) -> DryingOvenState:
    s = state['specs']
    passed = 'TemperatureRangeCelsius' in s and 'InternalVolumeLiters' in s
    return {**state, 'validation_passed': passed}

def finalize_order(state: DryingOvenState) -> DryingOvenState:
    if state.get('validation_passed'):
        print('Procurement workflow finalized for oven.')
    return state

graph = StateGraph(DryingOvenState)
graph.add_node('validate', validate_specs)
graph.add_node('finalize', finalize_order)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()