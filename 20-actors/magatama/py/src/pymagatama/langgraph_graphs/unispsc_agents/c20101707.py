from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class MachinePartState(TypedDict):
    part_id: str
    spec_data: dict
    validation_log: Annotated[Sequence[str], operator.add]
    is_approved: bool

def validate_specs(state: MachinePartState):
    log = []
    if 'material_composition' not in state['spec_data']:
        log.append('Missing material composition')
    if state.get('spec_data', {}).get('hardness_hrc', 0) < 50:
        log.append('Hardness below threshold')
    return {'validation_log': log}

def approval_check(state: MachinePartState):
    is_approved = len(state['validation_log']) == 0
    return {'is_approved': is_approved}

graph = StateGraph(MachinePartState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()