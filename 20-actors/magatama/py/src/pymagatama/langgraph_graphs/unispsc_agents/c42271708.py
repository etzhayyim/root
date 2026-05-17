from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class OxygenMaskState(TypedDict):
    part_number: str
    compliance_docs: List[str]
    is_validated: bool

def validate_certification(state: OxygenMaskState):
    state['is_validated'] = 'ISO_13485' in state.get('compliance_docs', [])
    return 'validate_certification'

def check_biocompatibility(state: OxygenMaskState):
    print(f'Checking biocompatibility for {state[\'part_number\']}')
    return {'is_validated': state['is_validated']}

graph = StateGraph(OxygenMaskState)
graph.add_node('validate', validate_certification)
graph.add_node('biocompatibility', check_biocompatibility)
graph.add_edge('validate', 'biocompatibility')
graph.add_edge('biocompatibility', END)
graph.set_entry_point('validate')
graph = graph.compile()