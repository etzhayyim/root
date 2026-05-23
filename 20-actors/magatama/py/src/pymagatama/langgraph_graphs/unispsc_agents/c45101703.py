from langgraph.graph import StateGraph, END
from typing import TypedDict
class CollatorState(TypedDict):
    equipment_id: str
    spec_check: bool
    validation_passed: bool
def validate_specs(state: CollatorState):
    print(f'Validating specs for {state["equipment_id"]}')
    return {"spec_check": True, "validation_passed": True}
def finalize_workflow(state: CollatorState):
    print('Workflow complete for printing collator.')
    return {"validation_passed": True}
graph = StateGraph(CollatorState)
graph.add_node("validate", validate_specs)
graph.add_node("finalize", finalize_workflow)
graph.set_entry_point("validate")
graph.add_edge("validate", "finalize")
graph.add_edge("finalize", END)
app = graph.compile()
