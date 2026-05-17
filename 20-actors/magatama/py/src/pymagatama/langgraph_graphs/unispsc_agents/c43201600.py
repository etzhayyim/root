from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    requirements: dict
    validation_results: Annotated[Sequence[str], operator.add]
    is_compliant: bool

def validate_specs(state: ProcurementState):
    res = "COMPLIANT" if "encryption" in state['requirements'] else "NON_COMPLIANT"
    return {'validation_results': [f"Spec verification: {res}"], 'is_compliant': res == "COMPLIANT"}

def route_procurement(state: ProcurementState):
    return "process_hardware" if state['is_compliant'] else "manual_review"

graph = StateGraph(ProcurementState)
graph.add_node("validate", validate_specs)
graph.add_node("process_hardware", lambda x: {"validation_results": ["Processing hardware order"]})
graph.add_node("manual_review", lambda x: {"validation_results": ["Escalating to manual procurement review"]})
graph.set_entry_point("validate")
graph.add_conditional_edges("validate", route_procurement)
graph.add_edge("process_hardware", END)
graph.add_edge("manual_review", END)
graph = graph.compile()