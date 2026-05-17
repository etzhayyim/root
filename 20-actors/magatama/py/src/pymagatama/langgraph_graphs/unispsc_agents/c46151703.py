from langgraph.graph import StateGraph, END
from typing import TypedDict
class GraphState(TypedDict):
    ink_formulation: str
    quality_check: bool
    compliance_score: float
def validate_formulation(state: GraphState):
    state['quality_check'] = 'nontoxic' in state['ink_formulation'].lower()
    return state
def assess_compliance(state: GraphState):
    state['compliance_score'] = 1.0 if state['quality_check'] else 0.0
    return state
graph = StateGraph(GraphState)
graph.add_node('validate', validate_formulation)
graph.add_node('compliance', assess_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()