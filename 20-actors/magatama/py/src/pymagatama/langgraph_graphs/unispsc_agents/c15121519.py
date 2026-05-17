from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class GasState(TypedDict):
    purity: float
    pressure: float
    is_safe: bool
    log: list[str]

def validate_gas_purity(state: GasState) -> GasState:
    state['is_safe'] = state['purity'] >= 99.999
    state['log'].append(f'Purity check: {state["purity"]}% (Safe: {state["is_safe"]})')
    return state

def check_pressure_vessel(state: GasState) -> GasState:
    if state['pressure'] > 200:
        state['is_safe'] = False
        state['log'].append('Pressure exceeded safety limits')
    return state

graph = StateGraph(GasState)
graph.add_node('validate_purity', validate_gas_purity)
graph.add_node('check_pressure', check_pressure_vessel)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_pressure')
graph.add_edge('check_pressure', END)
compiled_graph = graph.compile()