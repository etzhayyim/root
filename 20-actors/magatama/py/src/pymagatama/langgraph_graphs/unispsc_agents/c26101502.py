from typing import TypedDict
from langgraph.graph import StateGraph, END

class EngineState(TypedDict):
    specs: dict
    validation_status: str

def validate_pressure(state: EngineState):
    pressure = state['specs'].get('pressure', 0)
    status = 'PASS' if 0 < pressure <= 10 else 'FAIL'
    return {'validation_status': status}

workflow = StateGraph(EngineState)
workflow.add_node('validate', validate_pressure)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()
