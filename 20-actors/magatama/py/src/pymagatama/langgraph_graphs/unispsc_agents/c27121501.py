from typing import TypedDict
from langgraph.graph import StateGraph, END

class SpringState(TypedDict):
    spec_data: dict
    validation_log: list
    status: str

def validate_spring_specs(state: SpringState):
    log = []
    if state['spec_data'].get('spring_rate', 0) <= 0:
        log.append("Invalid spring rate")
    return {'validation_log': log, 'status': 'validated' if not log else 'failed'}

graph = StateGraph(SpringState)
graph.add_node('validate', validate_spring_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
