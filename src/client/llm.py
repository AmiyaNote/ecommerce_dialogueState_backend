from langchain.chat_models import init_chat_model

from conf.load_env import load_env, env_config

def build_llm():
    return init_chat_model(
        model=env_config["LLM_MODEL"],
        model_provider="openai",
        api_key=env_config["LLM_API_KEY"],
        base_url=env_config["LLM_BASE_URL"],
    )

llm = build_llm()

if __name__ == "__main__":
    response=llm.invoke("nihao")
    print(response.content)
