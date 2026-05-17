from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BookProcurementState(TypedDict):
    title: str
    age_group: str
    validation_checks: List[str]
    is_compliant: bool

def validate_materials(state: BookProcurementState):
    # Simulate material safety check for children's books
    print(f'Validating material safety for: {state["title"]}')
    return {"validation_checks": ["material_check_passed"], "is_compliant": True}

graph = StateGraph(BookProcurementState)
graph.add_node("validate_procurement", validate_materials)
graph.set_entry_point("validate_procurement")
graph.add_edge("validate_procurement", END)
graph = graph.compile()