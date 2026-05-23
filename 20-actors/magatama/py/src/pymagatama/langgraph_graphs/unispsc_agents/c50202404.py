from typing import TypedDict
from langgraph.graph import StateGraph, END

class LemonJuiceState(TypedDict):
    acidity: float
    brix: float
    is_pasteurized: bool
    passed: bool

def validate_quality(state: LemonJuiceState):
    # Industry standard: pH < 2.5 and Brix approx 7-9%
    is_valid = (state['acidity'] < 2.5) and (7.0 <= state['brix'] <= 9.0)
    return {'passed': is_valid}

workflow = StateGraph(LemonJuiceState)
workflow.add_node('validate', validate_quality)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()
