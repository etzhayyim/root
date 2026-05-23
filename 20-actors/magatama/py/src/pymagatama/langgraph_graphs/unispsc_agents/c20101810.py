from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class MiningPartsState(TypedDict):
    part_id: str
    spec_compliance: bool
    inspection_result: str
    workflow_log: List[str]

def validate_specs(state: MiningPartsState) -> MiningPartsState:
    # Logic to verify material grade and abrasion resistance
    state['spec_compliance'] = True
    state['workflow_log'].append('Specs validated')
    return state

def run_inspection(state: MiningPartsState) -> MiningPartsState:
    # Simulation of physical inspection process
    state['inspection_result'] = 'PASSED'
    state['workflow_log'].append('Physical inspection complete')
    return state

graph = StateGraph(MiningPartsState)
graph.add_node('validate', validate_specs)
graph.add_node('inspect', run_inspection)
graph.set_entry_point('validate')
graph.add_edge('validate', 'inspect')
graph.add_edge('inspect', END)

graph = graph.compile()
