from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class RippingToothState(TypedDict):
    part_numbers: List[str]
    spec_compliance: bool
    inspection_status: str

def validate_specs(state: RippingToothState):
    state['spec_compliance'] = all(['material' in p.lower() for p in state['part_numbers']])
    return {'spec_compliance': state['spec_compliance']}

def inspect_parts(state: RippingToothState):
    return {'inspection_status': 'Verified' if state['spec_compliance'] else 'Failed'}

graph = StateGraph(RippingToothState)
graph.add_node('validate', validate_specs)
graph.add_node('inspect', inspect_parts)
graph.add_edge('validate', 'inspect')
graph.add_edge('inspect', END)
graph.set_entry_point('validate')
app = graph.compile()
