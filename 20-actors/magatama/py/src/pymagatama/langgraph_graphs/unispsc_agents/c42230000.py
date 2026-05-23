from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class NutritionState(TypedDict):
    product_id: str
    quality_docs: List[str]
    is_compliant: bool

def validate_clinical_specs(state: NutritionState):
    required = ['GMP_Certificate', 'Nutritional_Analysis']
    state['is_compliant'] = all(doc in state['quality_docs'] for doc in required)
    return state

graph = StateGraph(NutritionState)
graph.add_node('validate', validate_clinical_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
app = graph.compile()
