from typing import TypedDict
from langgraph.graph import StateGraph, END

class LabUnitState(TypedDict):
    specs: dict
    is_compliant: bool
    validation_log: str

def validate_specs(state: LabUnitState):
    required = ['Material Compliance', 'Fire Rating']
    is_compliant = all(key in state['specs'] for key in required)
    return {'is_compliant': is_compliant, 'validation_log': 'Validation complete' if is_compliant else 'Missing fields'}

graph = StateGraph(LabUnitState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()