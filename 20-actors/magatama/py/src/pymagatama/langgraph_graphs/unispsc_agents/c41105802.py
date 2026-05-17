from typing import TypedDict
from langgraph.graph import StateGraph, END

class ReagentState(TypedDict):
    purity: float
    temp_log: list
    valid: bool

def validate_quality(state: ReagentState):
    return {'valid': state['purity'] >= 99.0}

def check_temp(state: ReagentState):
    return {'valid': all(t <= -20 for t in state['temp_log'])}

graph = StateGraph(ReagentState)
graph.add_node('validate', validate_quality)
graph.add_node('cold_chain', check_temp)
graph.set_entry_point('validate')
graph.add_edge('validate', 'cold_chain')
graph.add_edge('cold_chain', END)
graph = graph.compile()