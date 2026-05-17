from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class MountState(TypedDict):
    mount_specs: dict
    validation_passed: bool
    log: List[str]

def validate_specs(state: MountState):
    specs = state['mount_specs']
    passed = 'pull_force_kg' in specs and specs['pull_force_kg'] > 0
    return {'validation_passed': passed, 'log': [f'Validation result: {passed}']}

def finalize_order(state: MountState):
    return {'log': state['log'] + ['Order ready for procurement approval']}

graph_builder = StateGraph(MountState)
graph_builder.add_node('validate', validate_specs)
graph_builder.add_node('finalize', finalize_order)
graph_builder.set_entry_point('validate')
graph_builder.add_edge('validate', 'finalize')
graph_builder.add_edge('finalize', END)
graph = graph_builder.compile()