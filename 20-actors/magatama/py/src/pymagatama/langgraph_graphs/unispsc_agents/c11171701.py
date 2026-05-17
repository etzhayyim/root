from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class MineralProcurementState(TypedDict):
    commodity_id: str
    purity_level: float
    compliance_flag: bool
    messages: Annotated[Sequence[str], add_messages]

def validate_purity(state: MineralProcurementState):
    is_compliant = state['purity_level'] >= 99.5
    return {'compliance_flag': is_compliant, 'messages': [f'Purity check result: {is_compliant}']}

def route_by_compliance(state: MineralProcurementState):
    return 'process_order' if state['compliance_flag'] else 'flag_for_review'

graph = StateGraph(MineralProcurementState)
graph.add_node('validate', validate_purity)
graph.add_node('process_order', lambda s: {'messages': ['Order processed']})
graph.add_node('flag_for_review', lambda s: {'messages': ['Manual review required']})
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_compliance)
graph.add_edge('process_order', END)
graph.add_edge('flag_for_review', END)
graph = graph.compile()