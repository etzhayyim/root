from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class PetrochemicalState(TypedDict):
    purity_level: float
    safety_compliance: bool
    log_entries: Annotated[List[str], add_messages]

def validate_purity(state: PetrochemicalState):
    is_pure = state['purity_level'] >= 99.5
    return {'safety_compliance': is_pure, 'log_entries': [f'Purity check: {is_pure}']}

def check_regulations(state: PetrochemicalState):
    status = 'Pass' if state['safety_compliance'] else 'Fail: Review Required'
    return {'log_entries': [f'Regulatory review: {status}']}

graph = StateGraph(PetrochemicalState)
graph.add_node('validate', validate_purity)
graph.add_node('regulate', check_regulations)
graph.set_entry_point('validate')
graph.add_edge('validate', 'regulate')
graph.add_edge('regulate', END)
graph = graph.compile()
