from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class MiningBitState(TypedDict):
    bit_id: str
    material: str
    status: str
    logs: List[str]

def validate_bit(state: MiningBitState):
    # Simulate CAD/Spec validation logic
    state['logs'].append('Validating material hardness for mining bit.')
    return {'status': 'validated'}

def inspect_surface(state: MiningBitState):
    state['logs'].append('Running surface integrity inspection.')
    return {'status': 'inspected'}

workflow = StateGraph(MiningBitState)
workflow.add_node('validate', validate_bit)
workflow.add_node('inspect', inspect_surface)
workflow.set_entry_point('validate')
workflow.add_edge('validate', 'inspect')
workflow.add_edge('inspect', END)

graph = workflow.compile()
