from typing import TypedDict
from langgraph.graph import StateGraph, END

class DateProcurementState(TypedDict):
    origin: str
    moisture_level: float
    inspection_passed: bool

def validate_quality(state: DateProcurementState):
    if state['moisture_level'] > 20.0:
        return {'inspection_passed': False}
    return {'inspection_passed': True}

graph = StateGraph(DateProcurementState)
graph.add_node('validate_quality', validate_quality)
graph.set_entry_point('validate_quality')
graph.add_edge('validate_quality', END)
app = graph.compile()
