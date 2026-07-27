import logging
import os
import webbrowser
from typing import Any

logger = logging.getLogger("noray.llm.setup_api_keys")

PORTALS = {
    "openai": {
        "name": "OpenAI Developer Platform",
        "url": "https://platform.openai.com/api-keys",
        "env_var": "OPENAI_API_KEY"
    },
    "anthropic": {
        "name": "Anthropic Console",
        "url": "https://console.anthropic.com/settings/keys",
        "env_var": "ANTHROPIC_API_KEY"
    },
    "gemini": {
        "name": "Google AI Studio",
        "url": "https://aistudio.google.com/app/apikey",
        "env_var": "GOOGLE_API_KEY"
    },
    "openrouter": {
        "name": "OpenRouter Dashboard",
        "url": "https://openrouter.ai/keys",
        "env_var": "OPENROUTER_API_KEY"
    },
    "together": {
        "name": "Together AI Console",
        "url": "https://api.together.xyz/settings/api-keys",
        "env_var": "TOGETHER_API_KEY"
    },
    "mistral": {
        "name": "Mistral AI Console",
        "url": "https://console.mistral.ai/api-keys",
        "env_var": "MISTRAL_API_KEY"
    },
    "deepseek": {
        "name": "DeepSeek Platform",
        "url": "https://platform.deepseek.com/api_keys",
        "env_var": "DEEPSEEK_API_KEY"
    }
}

def mask_key(key: str) -> str:
    if not key:
        return "Not Configured"
    if len(key) <= 8:
        return "****"
    return f"{key[:4]}****{key[-4:]}"

def update_env_file(var_name: str, value: str):
    """Write or update value in local .env file securely."""
    env_path = ".env"
    lines = []

    # Read existing
    if os.path.exists(env_path):
        with open(env_path) as f:
            lines = f.readlines()

    updated = False
    new_lines = []
    for line in lines:
        if line.strip().startswith(f"{var_name}="):
            new_lines.append(f"{var_name}={value}\n")
            updated = True
        else:
            new_lines.append(line)

    if not updated:
        # Append newline if last line doesn't end with one
        if new_lines and not new_lines[-1].endswith("\n"):
            new_lines.append("\n")
        new_lines.append(f"{var_name}={value}\n")

    with open(env_path, "w") as f:
        f.writelines(new_lines)
    os.environ[var_name] = value

def test_key_health(provider_name: str, key: str) -> bool:
    """Test the newly added key via gateway provider health check."""
    from noray.llm.factory import LLMProviderFactory
    try:
        # Instantiate provider with temporary key
        # For gemini, we instantiate it
        provider_name_lower = provider_name.lower().strip()
        provider = LLMProviderFactory.get_provider(provider_name_lower)

        # Override key temporarily for checking
        original_key = getattr(provider, "api_key", None)
        provider.api_key = key

        healthy = provider.health()

        # Restore key
        if original_key is not None:
            provider.api_key = original_key

        return healthy
    except Exception:
        return False

def run_setup_wizard():
    print("=" * 60)
    print("      NORAY Hybrid LLM Gateway API Keys Setup Wizard")
    print("=" * 60)
    print("This wizard will open the official developer portals in your browser")
    print("to create keys, paste them below to configure your hybrid workspace.")
    print("-" * 60)

    results: dict[str, dict[str, Any]] = {}

    for name, info in PORTALS.items():
        print(f"\n[+] Provider: {info['name']}")
        current_val = os.getenv(info["env_var"], "")

        if current_val:
            print(f"    Current key: {mask_key(current_val)}")
            change = input("    Key already exists. Do you want to update it? (y/N): ").strip().lower()
            if change != 'y':
                results[name] = {"configured": True, "healthy": True, "masked": mask_key(current_val)}
                continue

        print(f"    Opening browser to: {info['url']}")
        webbrowser.open(info["url"])

        key = input(f"    Please paste the generated {info['name']} API key here (press Enter to skip): ").strip()

        if key:
            update_env_file(info["env_var"], key)
            print(f"    Key saved to .env: {mask_key(key)}")

            # Verify immediately
            print("    Testing connection health...")
            is_healthy = test_key_health(name, key)

            if is_healthy:
                print("    [OK] Connection test succeeded!")
                results[name] = {"configured": True, "healthy": True, "masked": mask_key(key)}
            else:
                print("    [WARN] Connection test failed or returned unconfigured status. Please check key validity.")
                results[name] = {"configured": True, "healthy": False, "masked": mask_key(key)}
        else:
            print("    Skipped.")
            results[name] = {"configured": False, "healthy": False, "masked": "Not Configured"}

    print("\n" + "=" * 60)
    print("                      Setup Summary")
    print("=" * 60)
    print(f"{'Provider':<15} | {'API Key Configured':<20} | {'Connection Test':<15}")
    print("-" * 60)
    for name, r in results.items():
        status = "Yes" if r["configured"] else "No"
        test = "PASSED" if r["healthy"] else "FAILED" if r["configured"] else "SKIPPED"
        print(f"{name.capitalize():<15} | {status:<20} | {test:<15}")
    print("=" * 60)
    print("NORAY configuration updated. Please restart the backend server to apply environment changes.")

if __name__ == "__main__":
    run_setup_wizard()
