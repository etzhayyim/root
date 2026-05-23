from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class ReagentState(TypedDict):
    material_id: str
    purity_level: float
    compliance_check: bool
    validation_log: Annotated[Sequence[str], operator.add]

def validate_purity(state: ReagentState):
    is_valid = state['purity_level'] >= 99.9
    return {'compliance_check': is_valid, 'validation_log': [f'Purity check: {is_valid}']}

def security_review(state: ReagentState):
    status = 'Pass' if state['compliance_check'] else 'Flagged for Review'
    return {'validation_log': [f'Security review status: {status}']}

graph = StateGraph(ReagentState)
graph.add_node('validate', validate_purity)
graph.add_node('security', security_review)
graph.set_entry_point('validate')
graph.add_edge('validate', 'security')
graph.add_edge('security', END)
app = graph.compile()
