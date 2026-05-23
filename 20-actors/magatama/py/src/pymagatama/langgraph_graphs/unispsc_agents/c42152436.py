from typing import TypedDict
from langgraph.graph import StateGraph, END

class InvestmentState(TypedDict):
    batch_id: str
    expansion_rate: float
    is_approved: bool

def validate_specs(state: InvestmentState):
    # Business logic for dental investment verification
    valid = (1.0 <= state['expansion_rate'] <= 2.5)
    return {'is_approved': valid}

workflow = StateGraph(InvestmentState)
workflow.add_node('validate', validate_specs)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()
