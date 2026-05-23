from typing import TypedDict
from langgraph.graph import StateGraph, END
class ReagentState(TypedDict):
    lot_number: str
    expiration_date: str
    temp_log: list[float]
    is_compliant: bool
def validate_reagent(state: ReagentState):
    temp_valid = all(2 <= t <= 8 for t in state['temp_log'])
    return {'is_compliant': temp_valid}
def check_expiry(state: ReagentState):
    return {'is_compliant': state['is_compliant']}
graph = StateGraph(ReagentState)
graph.add_node('validate', validate_reagent)
graph.add_node('expiry', check_expiry)
graph.add_edge('validate', 'expiry')
graph.add_edge('expiry', END)
graph.set_entry_point('validate')
graph = graph.compile()
