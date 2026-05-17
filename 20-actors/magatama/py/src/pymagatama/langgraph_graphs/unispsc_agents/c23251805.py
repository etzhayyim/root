from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ForgingDieState(TypedDict):
    specs: dict
    approved: bool
    validation_logs: List[str]

def validate_specs(state: ForgingDieState):
    logs = []
    if state['specs'].get('hardness', 0) < 50:
        logs.append('Insufficient hardness')
    return {'validation_logs': logs, 'approved': len(logs) == 0}

graph = StateGraph(ForgingDieState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()