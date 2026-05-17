from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class MiningPartsState(TypedDict):
    part_id: str
    inspection_status: str
    compliance_checks: List[str]
    approved: bool

def validate_part(state: MiningPartsState) -> MiningPartsState:
    print(f'Validating part: {state.part_id}')
    state['compliance_checks'].append('ISO_MINING_STD')
    state['inspection_status'] = 'PENDING_METALLURGICAL_ANALYSIS'
    return state

def check_compliance(state: MiningPartsState) -> MiningPartsState:
    if 'ISO_MINING_STD' in state['compliance_checks']:
        state['approved'] = True
        state['inspection_status'] = 'PASSED'
    return state

graph = StateGraph(MiningPartsState)
graph.add_node('validate', validate_part)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)

compiled_graph = graph.compile()