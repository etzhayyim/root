from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class MineralState(TypedDict):
    batch_id: str
    purity: float
    origin: str
    risk_flag: bool
    history: List[str]

def validate_quality(state: MineralState) -> MineralState:
    if state['purity'] < 0.95:
        state['history'].append('Quality check failed: Insufficient purity.')
        state['risk_flag'] = True
    return state

def check_sanctions(state: MineralState) -> MineralState:
    if state['origin'] in ['sanctioned_country_list']:
        state['history'].append('Compliance check failed: Sanctioned origin.')
        state['risk_flag'] = True
    return state

graph = StateGraph(MineralState)
graph.add_node('validate_quality', validate_quality)
graph.add_node('check_sanctions', check_sanctions)
graph.set_entry_point('validate_quality')
graph.add_edge('validate_quality', 'check_sanctions')
graph.add_edge('check_sanctions', END)

# Compile the graph
app = graph.compile()