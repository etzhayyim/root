from typing import TypedDict, Annotated, List
import operator
from langgraph.graph import StateGraph, END

class ReagentState(TypedDict):
    lot_number: str
    temperature_logs: List[float]
    is_compliant: bool
    next_action: str

def validate_cold_chain(state: ReagentState) -> ReagentState:
    compliant = all(temp <= 8.0 for temp in state['temperature_logs'])
    return {**state, 'is_compliant': compliant, 'next_action': 'release' if compliant else 'quarantine'}

def process_reagent(state: ReagentState) -> ReagentState:
    if state['is_compliant']:
        return {**state, 'next_action': 'ship'}
    return {**state, 'next_action': 'notify_qc'}

graph = StateGraph(ReagentState)
graph.add_node('validate', validate_cold_chain)
graph.add_node('process', process_reagent)
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')
graph = graph.compile()