from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class MineralProcessState(TypedDict):
    material_id: str
    composition_data: dict
    validation_passed: bool
    log: Annotated[Sequence[str], operator.add]

def validate_purity(state: MineralProcessState):
    purity = state['composition_data'].get('purity', 0)
    passed = purity >= 95.0
    return {'validation_passed': passed, 'log': [f'Purity check: {purity}% - Result: {passed}']}

def process_ore(state: MineralProcessState):
    return {'log': ['Processing ore composition for industrial safety compliance.']}

graph = StateGraph(MineralProcessState)
graph.add_node('validate', validate_purity)
graph.add_node('process', process_ore)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)

compiled_graph = graph.compile()