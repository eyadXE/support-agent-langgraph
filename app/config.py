"""Central config: env loading, model instance, shared constants."""
from dotenv import load_dotenv
from langchain_openrouter import ChatOpenRouter

load_dotenv()

MODEL_NAME = "nvidia/nemotron-3.5-lightning"

model = ChatOpenRouter(
    model=MODEL_NAME,
    temperature=0,
)
