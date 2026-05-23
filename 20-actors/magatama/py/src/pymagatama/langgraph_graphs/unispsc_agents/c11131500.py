from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
import operator

class MineralProcessState(TypedDict):
    material_id: str
    hardness_check: bool
    purity_level: float
    validation_logs: Annotated[Sequence[str], operator.add]

def check_physical_specs(state: MineralProcessState):
    # Simulated hardening and purity validation
    passed = state['purity_level'] >= 98.0
    return {'hardness_check': passed, 'validation_logs': ['Hardness/Purity specs verified against ISO standards']}

def approval_node(state: MineralProcessState):
    status = 'Approved' if state['hardness_check'] else 'Rejected'
    return {'validation_logs': [f'Final processing status: {status}']}

graph = StateGraph(MineralProcessState)
graph.add_node('specs', check_physical_specs)
graph.add_node('approval', approval_node)
graph.set_entry_point('specs')
graph.add_edge('specs', 'approval')
graph.add_edge('approval', END)
graph = graph.compile()
