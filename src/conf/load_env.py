from dotenv import load_dotenv, dotenv_values


def load_env() -> dict:

    load_dotenv( override=True)
    data = dotenv_values()
    import os
    return {key: os.getenv(key, value) for key, value in data.items() if key}


env_config = load_env()

if __name__ == "__main__":
    print(env_config)
    print(env_config["DATABASE_URL"])