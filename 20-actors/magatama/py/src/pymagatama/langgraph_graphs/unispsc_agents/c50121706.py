from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    product_name: str
    temp_log: List[float]
    safety_verified: bool

def check_temp(state: ProcurementState):
    avg_temp = sum(state['temp_log']) / len(state['temp_log']) if state['temp_log'] else 0
    return {'safety_verified': avg_temp <= -18.0}

def finalize(state: ProcurementState):
    return {'safety_verified': state['safety_verified']}

graph = StateGraph(ProcurementState)
graph.add_node('check_temp', check_temp)
graph.add_node('finalize', finalize)
graph.set_entry_point('check_temp')
graph.add_edge('check_temp', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()