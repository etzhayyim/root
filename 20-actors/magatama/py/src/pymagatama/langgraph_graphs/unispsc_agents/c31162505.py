from typing import TypedDict, Annotated
import operator
from langgraph.graph import StateGraph, END

class MountState(TypedDict):
    part_specs: dict
    validation_results: Annotated[list, operator.add]
    is_approved: bool

def validate_magnetics(state: MountState):
    pull_force = state['part_specs'].get('force', 0)
    valid = pull_force > 50
    return {'validation_results': [f'Force check: {valid}'], 'is_approved': valid}

def structural_check(state: MountState):
    material = state['part_specs'].get('material', 'plastic')
    status = material == 'steel'
    return {'validation_results': [f'Material check: {status}']}

graph = StateGraph(MountState)
graph.add_node('validate_magnetics', validate_magnetics)
graph.add_node('structural_check', structural_check)
graph.set_entry_point('validate_magnetics')
graph.add_edge('validate_magnetics', 'structural_check')
graph.add_edge('structural_check', END)
graph = graph.compile()
