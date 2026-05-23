from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class GasState(TypedDict):
    purity: float
    pressure: float
    safety_check: bool
    log: Annotated[Sequence[str], operator.add]

def validate_gas_purity(state: GasState) -> GasState:
    is_pure = state['purity'] >= 99.99
    return {'safety_check': is_pure, 'log': [f'Purity check: {is_pure}']}

def verify_pressure(state: GasState) -> GasState:
    is_safe = state['pressure'] < 200
    return {'safety_check': state['safety_check'] and is_safe, 'log': [f'Pressure check: {is_safe}']}

graph = StateGraph(GasState)
graph.add_node('validate', validate_gas_purity)
graph.add_node('pressure', verify_pressure)
graph.set_entry_point('validate')
graph.add_edge('validate', 'pressure')
graph.add_edge('pressure', END)
compile_graph = graph.compile()
