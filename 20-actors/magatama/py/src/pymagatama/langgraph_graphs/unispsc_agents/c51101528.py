from typing import TypedDict, Annotated, List
import operator
from langgraph.graph import StateGraph, END

class ReagentState(TypedDict):
    reagent_id: str
    purity_level: float
    validation_logs: Annotated[List[str], operator.add]
    is_approved: bool

def validate_purity(state: ReagentState):
    if state['purity_level'] >= 99.0:
        return {'validation_logs': ['Purity check passed'], 'is_approved': True}
    return {'validation_logs': ['Purity check failed'], 'is_approved': False}

def audit_log(state: ReagentState):
    print(f'Audit for {state.get(reagent_id)}: {state.get(validation_logs)}')
    return {}

graph = StateGraph(ReagentState)
graph.add_node('validate', validate_purity)
graph.add_node('audit', audit_log)
graph.add_edge('validate', 'audit')
graph.add_edge('audit', END)
graph.set_entry_point('validate')
app = graph.compile()