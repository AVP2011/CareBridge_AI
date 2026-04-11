import json
import os

NOTEBOOK_PATH = "d:/Projrcts/CareBridge_AI-main/kaggle notebook/carebridge-v3.ipynb"

def patch_notebook():
    if not os.path.exists(NOTEBOOK_PATH):
        print(f"Error: {NOTEBOOK_PATH} not found.")
        return

    with open(NOTEBOOK_PATH, 'r', encoding='utf-8') as f:
        nb = json.load(f)

    for cell in nb['cells']:
        # Patch Cell 6 (Pre-download Model)
        if "Pre-downloading MedGemma model" in "".join(cell.get('source', [])):
            cell['source'] = [
                "import os\n",
                "import subprocess\n",
                "import torch\n",
                "from huggingface_hub import login, snapshot_download\n",
                "from transformers import AutoTokenizer, AutoModelForCausalLM\n",
                "from kaggle_secrets import UserSecretsClient\n",
                "\n",
                "# 1. Setup Speed & Storage\n",
                "os.environ[\"HF_HOME\"] = \"/kaggle/working/hf_cache\"\n",
                "os.environ[\"HF_HUB_ENABLE_HF_TRANSFER\"] = \"1\"\n",
                "!pip install -q hf_transfer\n",
                "\n",
                "print(\"🧠 Pre-downloading Gemma-2 2B (Optimized Logic)...\\n\")\n",
                "\n",
                "# 2. Space Check\n",
                "print(\"📊 Checking disk space...\")\n",
                "res = subprocess.run([\"df\", \"-h\", \"/kaggle/working\"], capture_output=True, text=True)\n",
                "print(res.stdout)\n",
                "\n",
                "# 3. Model Info\n",
                "MODEL_NAME = \"google/gemma-2-2b-it\"\n",
                "print(f\"📦 Target Model: {MODEL_NAME}\")\n",
                "print(\"⚠️  IMPORTANT: Ensure Internet=ON and you accepted the license on HuggingFace.\\n\")\n",
                "\n",
                "# 4. Authentication\n",
                "try:\n",
                "    hf_token = UserSecretsClient().get_secret(\"HF_TOKEN\")\n",
                "    if hf_token:\n",
                "        login(hf_token)\n",
                "        print(\"✅ HF Auth Successful\")\n",
                "    else:\n",
                "        print(\"❌ HF_TOKEN not found in Kaggle Secrets.\")\n",
                "except Exception as e:\n",
                "    print(f\"⚠️  Auth status: {e}\")\n",
                "\n",
                "# 5. Reliable High-Speed Download\n",
                "print(f\"\\n📥 Fetching {MODEL_NAME} using hf_transfer...\")\n",
                "try:\n",
                "    snapshot_download(\n",
                "        repo_id=MODEL_NAME,\n",
                "        local_dir_use_symlinks=False,\n",
                "        cache_dir=os.environ[\"HF_HOME\"]\n",
                "    )\n",
                "    print(\"✅ Download complete!\\n\")\n",
                "    \n",
                "    # Quick Memory Check\n",
                "    print(\"🧪 Verifying loading capability...\")\n",
                "    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)\n",
                "    model = AutoModelForCausalLM.from_pretrained(\n",
                "        MODEL_NAME,\n",
                "        torch_dtype=torch.bfloat16,\n",
                "        device_map=\"auto\"\n",
                "    )\n",
                "    print(\"✅ Model loaded. Clearing memory for server startup...\")\n",
                "    del model\n",
                "    del tokenizer\n",
                "    torch.cuda.empty_cache()\n",
                "    print(\"🧹 Memory Ready.\")\n",
                "except Exception as e:\n",
                "    print(f\"❌ ERROR: {e}\")"
            ]
            print("Patched Cell 6.")

        # Patch Cell 8 (Start Server)
        if "Starting FastAPI server" in "".join(cell.get('source', [])):
            # Update to avoid redundant pip installs if possible, or keep as is with better environment propagation
            cell['source'] = [
                "import subprocess\n",
                "import time\n",
                "import os\n",
                "import requests\n",
                "\n",
                "BACKEND = \"/kaggle/working/carebridge\"\n",
                "CACHE = \"/kaggle/working/hf_cache\"\n",
                "LOG_FILE = \"/kaggle/working/server.log\"\n",
                "\n",
                "print(\"🚀 Starting FastAPI Server...\\n\")\n",
                "\n",
                "# 1. Safety Cleanup\n",
                "subprocess.run([\"pkill\", \"-f\", \"uvicorn\"], capture_output=True)\n",
                "time.sleep(2)\n",
                "\n",
                "# 2. Environment Setup\n",
                "env = os.environ.copy()\n",
                "env.update({\n",
                "    \"PYTHONPATH\": BACKEND,\n",
                "    \"HF_HOME\": CACHE,\n",
                "    \"HF_HUB_ENABLE_HF_TRANSFER\": \"1\",\n",
                "    \"HUGGINGFACE_HUB_CACHE\": f\"{CACHE}/hub\",\n",
                "    \"TRANSFORMERS_CACHE\": f\"{CACHE}/hub\",\n",
                "})\n",
                "\n",
                "# Pass HF_TOKEN to server context\n",
                "try:\n",
                "    from kaggle_secrets import UserSecretsClient\n",
                "    env[\"HF_TOKEN\"] = UserSecretsClient().get_secret(\"HF_TOKEN\")\n",
                "except: pass\n",
                "\n",
                "# 3. Background Startup\n",
                "with open(LOG_FILE, \"w\") as f:\n",
                "    process = subprocess.Popen(\n",
                "        [\"python\", \"-m\", \"uvicorn\", \"main:app\", \"--host\", \"0.0.0.0\", \"--port\", \"8000\"],\n",
                "        cwd=BACKEND, stdout=f, stderr=subprocess.STDOUT, env=env\n",
                "    )\n",
                "\n",
                "print(f\"   📝 Logs: {LOG_FILE}\")\n",
                "print(\"   ⏳ Waiting for initialization...\")\n",
                "\n",
                "# 4. Health Check Loop\n",
                "for i in range(1, 40):\n",
                "    try:\n",
                "        r = requests.get(\"http://localhost:8000/\", timeout=2)\n",
                "        if r.status_code == 200:\n",
                "            print(f\"\\n✅ Server is LIVE! Response: {r.json()}\")\n",
                "            break\n",
                "    except:\n",
                "        print(f\"   [{i*5}s] still loading...\", end=\"\\r\")\n",
                "        time.sleep(5)\n",
                "else:\n",
                "    print(\"\\n⚠️  Server timeout. Check logs: !tail -50 /kaggle/working/server.log\")"
            ]
            print("Patched Cell 8.")

    with open(NOTEBOOK_PATH, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=1)

if __name__ == "__main__":
    patch_notebook()
    print("Notebook patched successfully.")
