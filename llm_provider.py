import os

class LLMProvider:
    def __init__(self):
        self.provider = os.environ.get("LLM_PROVIDER", "mock")

        if self.provider == "openai":
            from openai import OpenAI
            self.client = OpenAI()

        elif self.provider == "anthropic":
            import anthropic
            self.client = anthropic.Anthropic(
                api_key=os.environ.get("ANTHROPIC_API_KEY")
            )

        elif self.provider == "ollama":
            import requests
            self.client = requests
    def _mock_generate(self, system, history):
        if "name" in system.lower():
            return "Nice to meet you! What's your email?"

        if "email" in system.lower():
            return "Got it! Could you share your phone number?"

        if "tech stack" in system.lower():
            return "Great! Let's begin technical questions."

        if "generate" in system.lower():
            return '["Explain Python OOP concepts", "What is REST API?", "How does Django ORM work?"]'

        return "Thanks for your response!"

    def generate(self, system, history):
        if self.provider == "openai":
            return self._openai_generate(system, history)

        elif self.provider == "anthropic":
            return self._anthropic_generate(system, history)

        elif self.provider == "ollama":
            return self._ollama_generate(system, history)

    # ---------- OpenAI ----------
    def _openai_generate(self, system, history):
        messages = [{"role": "system", "content": system}] + history[-20:]

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()

    # ---------- Anthropic ----------
    def _anthropic_generate(self, system, history):
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=512,
            system=system,
            messages=history[-20:],
        )
        return response.content[0].text.strip()

    # ---------- Ollama ----------
    def _ollama_generate(self, system, history):
        import requests

        prompt = system + "\n\n" + "\n".join([m["content"] for m in history])

        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3",
                "prompt": prompt,
                "stream": False,
            },
        )
        return response.json()["response"]