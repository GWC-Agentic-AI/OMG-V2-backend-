from pydantic import BaseModel

class GenerateQuizRequest(BaseModel):
    num_of_questions: int

class TranslateRequest(BaseModel):
    lang_code: str
    quiz_id:int
