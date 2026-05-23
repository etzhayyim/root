from typing import TypedDict
from langgraph.graph import StateGraph, END

class LabelState(TypedDict):
    label_type: str
    compliance_checked: bool
    approved: bool

def validate_medical_grade(state: LabelState):
    print(f'Validating compliance for: {state["label_type"]}')
    return {"compliance_checked": True}

def approval_step(state: LabelState):
    return {"approved": state["compliance_checked"]}

graph = StateGraph(LabelState)
graph.add_node("validate", validate_medical_grade)
graph.add_node("approval", approval_step)
graph.set_entry_point("validate")
graph.add_edge("validate", "approval")
graph.add_edge("approval", END)
app = graph.compile()
