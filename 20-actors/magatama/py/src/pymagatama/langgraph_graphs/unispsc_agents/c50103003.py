from typing import TypedDict
from langgraph.graph import StateGraph, END
class SupplyState(TypedDict):
    temp: float
    status: str
def check_temp(state: SupplyState):
    return {'status': 'Approved' if state['temp'] <= -18.0 else 'Rejected'}
builder = StateGraph(SupplyState)
builder.add_node('check_temp', check_temp)
builder.set_entry_point('check_temp')
builder.add_edge('check_temp', END)
graph = builder.compile()