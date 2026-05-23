from typing import TypedDict
from langgraph.graph import StateGraph, END

class PumpState(TypedDict):
    pressure_req: float
    flow_rate: float
    validation_status: bool

def validate_specs(state: PumpState):
    state['validation_status'] = state['pressure_req'] < 1000 and state['flow_rate'] > 0
    return state

def route_logic(state: PumpState):
    return 'process' if state['validation_status'] else END

graph = StateGraph(PumpState)
graph.add_node('validate', validate_specs)
graph.add_node('process', lambda s: s)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_logic, {'process': 'process', '__end__': END})
graph.add_edge('process', END)
graph = graph.compile()
