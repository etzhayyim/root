from typing import TypedDict, Annotated
import operator
from langgraph.graph import StateGraph, END

class MineralIngestState(TypedDict):
    batch_id: str
    purity_levels: list[float]
    is_compliant: bool

def validate_purity(state: MineralIngestState):
    avg_purity = sum(state['purity_levels']) / len(state['purity_levels'])
    return {'is_compliant': avg_purity >= 98.5}

def process_mineral(state: MineralIngestState):
    if state['is_compliant']:
        return {'batch_id': f'PROC-{state['batch_id']}'}
    return {'batch_id': f'REJECT-{state['batch_id']}'}

graph = StateGraph(MineralIngestState)
graph.add_node('validate', validate_purity)
graph.add_node('process', process_mineral)
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')
graph = graph.compile()