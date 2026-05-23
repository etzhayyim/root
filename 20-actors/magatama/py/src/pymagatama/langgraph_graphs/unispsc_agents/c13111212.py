from typing import TypedDict, List, Annotated
from langgraph.graph import StateGraph, END
import operator

class DrillBitState(TypedDict):
    bit_id: str
    specs: dict
    validation_log: Annotated[List[str], operator.add]
    is_approved: bool

def validate_bit_hardness(state: DrillBitState) -> DrillBitState:
    hardness = state['specs'].get('hardness', 0)
    if hardness >= 9.5:
        state['validation_log'] = ['Hardness validated as industrial grade.']
    else:
        state['validation_log'] = ['Hardness below threshold.']
    return state

def check_thermal_rating(state: DrillBitState) -> DrillBitState:
    rating = state['specs'].get('thermal_stability', 0)
    if rating > 800:
        state['validation_log'] = ['Thermal stability verified.']
        state['is_approved'] = True
    else:
        state['is_approved'] = False
    return state

graph = StateGraph(DrillBitState)
graph.add_node('validate_hardness', validate_bit_hardness)
graph.add_node('check_thermal', check_thermal_rating)
graph.set_entry_point('validate_hardness')
graph.add_edge('validate_hardness', 'check_thermal')
graph.add_edge('check_thermal', END)

app = graph.compile()
