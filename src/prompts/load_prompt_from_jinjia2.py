from pathlib import Path


def load_prompt_from_jinja2(prompt_file_name: str) -> str:
    """
    从固定的 jinja2 目录读取提示词模板。

    约定:
    - 模板目录固定为 src/prompts/jinja2
    - 模板文件后缀固定为 .jinja2
    - 调用方只传模板名，例如 turn_plan
    """
    prompts_dir = Path(__file__).resolve().parent / "jinja2"
    prompt_suffix = ".jinja2"
    prompt_file_path = prompts_dir / f"{prompt_file_name}{prompt_suffix}"

    if not prompt_file_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_file_path}")

    return prompt_file_path.read_text(encoding="utf-8")



if __name__ == "__main__":
    print(load_prompt_from_jinja2("turn_plan"))
