from pydantic import BaseModel


class KnowledgeIntent(BaseModel):
    intent: str