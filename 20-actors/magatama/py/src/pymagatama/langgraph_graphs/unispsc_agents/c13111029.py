from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class MineralState(TypedDict):
    raw_input: dict
    compliance_validated: bool
    purity_score: float
    messages: Annotated[Sequence[str], add_messages]

def validate_compliance(state: MineralState):
    # Simulated compliance logic for raw mineral procurement
    origin = state['raw_input'].get('origin', 'unknown')
    is_compliant = origin not in ['sanctioned_region_x']
    return {'compliance_validated': is_compliant, 'messages': ['Compliance check completed']}

def process_purity(state: MineralState):
    # Simulated technical analysis logic
    purity = state['raw_input'].get('purity_value', 0.0)
    return {'purity_score': purity, 'messages': ['Purity analysis finalized']}

graph = StateGraph(MineralState)
graph.add_node('compliance', validate_compliance)
graph.add_node('analysis', process_purity)
graph.set_entry_point('compliance')
graph.add_edge('compliance', 'analysis')
graph.add_edge('analysis', END)
graph = graph.compile()
