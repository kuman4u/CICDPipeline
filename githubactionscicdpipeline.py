import os
import re

from dotenv import load_dotenv
from openai import OpenAI


def strip_code_fences(text: str) -> str:
    """
    Extract YAML from a model response by removing ```yaml ... ``` fences
    if they exist.
    """
    # Remove opening fence like ``` or ```yaml
    text = re.sub(r"```(?:yaml)?\n?", "", text)
    # Remove trailing fence ```
    text = re.sub(r"\n?```$", "", text.strip())
    return text.strip()


def main() -> None:
    # Load API key from .env file
    load_dotenv()
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        raise ValueError("OPENAI_API_KEY is missing. Add it to your .env file.")

    client = OpenAI(api_key=openai_key)

    # Step 1: Generate GitHub Actions YAML
    prompt_generate = """
Generate a GitHub Actions pipeline in YAML for a Python project.
The workflow should:
- Run on push to the main branch
- Lint the code using flake8
- Run tests using pytest
- Include a mocked deployment step using `echo`
""".strip()

    response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[{"role": "user", "content": prompt_generate}],
    )

    generated_yaml = response.choices[0].message.content or ""
    print("Generated GitHub Actions Workflow:\n")
    print(generated_yaml)

    # Step 2: Introduce a YAML error
    broken_yaml = generated_yaml.replace(
        "- name: Lint with flake8",
        "   - name: Lint with flake8",
    )
    print("\nBroken YAML with Indentation Error:\n")
    print(broken_yaml)

    # Step 3: Ask GPT to fix the YAML
    prompt_debug = f"""
I have a GitHub Actions YAML file and I'm getting an error saying:
'YAML file does not conform to schema: Unexpected value'.

Here is the broken YAML:
---
{broken_yaml}
---
Can you help identify and fix the issue?
""".strip()

    response_fix = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[{"role": "user", "content": prompt_debug}],
    )

    raw_output = response_fix.choices[0].message.content or ""
    fixed_yaml = strip_code_fences(raw_output)

    print("Cleaned Fixed YAML by GPT:\n")
    print(fixed_yaml)

    # Step 4: Save the YAML file
    os.makedirs(".github/workflows", exist_ok=True)
    with open(".github/workflows/python-ci.yml", "w", encoding="utf-8") as f:
        f.write(fixed_yaml + "\n")

    print("Saved to .github/workflows/python-ci.yml")


if __name__ == "__main__":
    main()
