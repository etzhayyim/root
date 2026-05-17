from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class ChemicalIngestState(TypedDict):
    batch_id: str
    purity: float
    safety_clearance: bool
    process_logs: Annotated[Sequence[str], operator.add]

def validate_purity(state: ChemicalIngestState) -> ChemicalIngestState:
    if state['purity'] < 99.9:
        return {'process_logs': ['Purity requirement not met for high-grade synthesis']}
    return {'process_logs': ['Purity validation passed']}

def safety_gate(state: ChemicalIngestState) -> str:
    if not state.get('safety_clearance', False):
        return 'END'
    return 'process'

def process_chemical(state: ChemicalIngestState) -> ChemicalIngestState:
    return {'process_logs': ['Advanced chemical synthesis routing initiated']}

graph = StateGraph(ChemicalIngestState)
graph.add_node('validate', validate_purity)
graph.add_node('process', process_chemical)
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')
graph = graph.compile()