from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class GasMaskState(TypedDict):
    model_number: str
    certification_docs: List[str]
    is_compliant: bool

def validate_specs(state: GasMaskState):
    # Simulate NIOSH/EN certification check logic
    state['is_compliant'] = 'NIOSH' in state['certification_docs'][0] if state['certification_docs'] else False
    return state

graph = StateGraph(GasMaskState)
graph.add_node('validator', validate_specs)
graph.add_edge('validator', END)
graph.set_entry_point('validator')
graph = graph.compile()