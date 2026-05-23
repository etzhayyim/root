from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class MiningToolState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    approved: bool

def validate_tool_specs(state: MiningToolState):
    errors = []
    if state['spec_data'].get('hrc_hardness', 0) < 55:
        errors.append('Hardness below industrial mining standard requirements.')
    return {'validation_errors': errors, 'approved': len(errors) == 0}

graph = StateGraph(MiningToolState)
graph.add_node('validate', validate_tool_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
