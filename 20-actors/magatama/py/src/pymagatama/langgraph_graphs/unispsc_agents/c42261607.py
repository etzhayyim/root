from typing import TypedDict
from langgraph.graph import StateGraph, END

class AutopsyBagState(TypedDict):
    spec_data: dict
    validation_results: list
    is_compliant: bool

def validate_materials(state: AutopsyBagState):
    bio_label = state['spec_data'].get('biohazard_labeling_compliance', False)
    leak_proof = state['spec_data'].get('leak_proof_test_standard', False)
    return {"validation_results": ["bio_compliance", "leak_test_passed"] if (bio_label and leak_proof) else ["failed"]}

def finalize_order(state: AutopsyBagState):
    return {"is_compliant": len(state['validation_results']) > 1}

graph = StateGraph(AutopsyBagState)
graph.add_node("validate", validate_materials)
graph.add_node("finalize", finalize_order)
graph.set_entry_point("validate")
graph.add_edge("validate", "finalize")
graph.add_edge("finalize", END)
graph = graph.compile()
