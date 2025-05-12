from typing import TypedDict, List, Dict

class State(TypedDict):
  response: str
  user_message: str
  chat_answer: List[Dict[str, str]]
  final_answer: str
