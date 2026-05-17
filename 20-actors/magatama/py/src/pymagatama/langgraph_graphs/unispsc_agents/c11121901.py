from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
import operator

class MineralState(TypedDict):
    raw_batch: dict
    purity_validated: bool
    impurity_report: List[str]
    log: Annotated[List[str], operator.add]

def validate_chemistry(state: MineralState):
    batch = state['raw_batch']
    purity = batch.get('purity', 0)
    valid = purity > 98.0
    return {'purity_validated': valid, 'log': [f'Chemistry validated: {valid}']}

def check_impurities(state: MineralState):
    impurities = state['raw_batch'].get('impurities', [])
    issues = [i for i in impurities if i['level'] > 0.01]
    return {'impurity_report': issues, 'log': [f'Found {len(issues)} impurity concerns']}

graph = StateGraph(MineralState)
graph.add_node('chemistry', validate_chemistry)
graph.add_node('impurities', check_impurities)
graph.set_entry_point('chemistry')
graph.add_edge('chemistry', 'impurities')
graph.add_edge('impurities', END)
graph = graph.compile()