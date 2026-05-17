from typing import TypedDict
from langgraph.graph import StateGraph, END

class ReagentState(TypedDict):
    lot_number: str
    temperature_logs: list[float]
    is_compliant: bool

def validate_cold_chain(state: ReagentState):
    avg_temp = sum(state['temperature_logs']) / len(state['temperature_logs'])
    return {'is_compliant': 2.0 <= avg_temp <= 8.0}

def check_regulatory(state: ReagentState):
    return {'is_compliant': state['is_compliant'] and len(state['lot_number']) > 5}

graph = StateGraph(ReagentState)
graph.add_node('validate_chain', validate_cold_chain)
graph.add_node('check_reg', check_regulatory)
graph.set_entry_point('validate_chain')
graph.add_edge('validate_chain', 'check_reg')
graph.add_edge('check_reg', END)
graph = graph.compile()