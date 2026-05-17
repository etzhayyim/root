from typing import TypedDict
from langgraph.graph import StateGraph, END

class FlaringState(TypedDict):
    tool_specs: dict
    is_compliant: bool
    validation_report: str

def validate_specs(state: FlaringState):
    specs = state['tool_specs']
    is_compliant = 'diameter' in specs and 'angle' in specs
    return {'is_compliant': is_compliant, 'validation_report': 'Validated' if is_compliant else 'Missing parameters'}

graph = StateGraph(FlaringState)
graph.add_node('validation', validate_specs)
graph.set_entry_point('validation')
graph.add_edge('validation', END)
graph = graph.compile()