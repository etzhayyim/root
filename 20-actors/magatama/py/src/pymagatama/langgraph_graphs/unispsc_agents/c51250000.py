from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class VetSuppState(TypedDict):
    product_name: str
    ingredients: List[str]
    compliance_docs: List[str]
    is_safe: bool

def validate_ingredients(state: VetSuppState):
    # Business logic for ingredient safety check
    return {'is_safe': 'toxic_substance' not in state['ingredients']}

def check_compliance(state: VetSuppState):
    # Verify necessary regulatory documents
    return {'compliance_docs': state.get('compliance_docs', []) + ['GMP_Verified']}

graph = StateGraph(VetSuppState)
graph.add_node('ingredient_check', validate_ingredients)
graph.add_node('compliance_check', check_compliance)
graph.add_edge('ingredient_check', 'compliance_check')
graph.add_edge('compliance_check', END)
graph.set_entry_point('ingredient_check')
graph = graph.compile()
