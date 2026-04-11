import json

nb_path = r'kaggle notebook\carebridge-kaggle-notebook-improved.ipynb'

with open(nb_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

for i, cell in enumerate(nb.get('cells', [])):
    if cell.get('cell_type') != 'code':
        continue
    
    if isinstance(cell['source'], list):
        src = ''.join(cell['source'])
    else:
        src = cell['source']
    
    if 'ngrok' in src.lower() and 'NGROK_AUTH_TOKEN' in src:
        cell['source'] = '''from pyngrok import ngrok
import time

# Your ngrok auth token (get from https://dashboard.ngrok.com/get-started/your-authtoken)
NGROK_AUTH_TOKEN = "YOUR_NGROK_TOKEN_HERE"

if NGROK_AUTH_TOKEN == "YOUR_NGROK_TOKEN_HERE" or not NGROK_AUTH_TOKEN.strip():
    print("You need to set your ngrok token!\\n")
    print("Steps:\\n")
    print("1. Go to: https://dashboard.ngrok.com/get-started/your-authtoken")
    print("2. Sign up (free)")
    print("3. Copy your auth token")
    print("4. Replace YOUR_NGROK_TOKEN_HERE above with your token")
    print("5. Re-run this cell\\n")
else:
    print("Setting up ngrok tunnel...\\n")

    # Kill any existing tunnels
    ngrok.kill()
    time.sleep(2)

    # Set auth token
    ngrok.set_auth_token(NGROK_AUTH_TOKEN)

    # Create tunnel
    try:
        tunnel = ngrok.connect(8000, "http")
        public_url = tunnel.public_url

        print("Ngrok tunnel created!\\n")
        print("=" * 60)
        print(f"PUBLIC URL: {public_url}")
        print("=" * 60)
        print(f"\\nAPI Documentation: {public_url}/docs")
        print(f"Health Check: {public_url}/")
        print(f"\\nUse this URL in your frontend:\\n")
        print(f"   const API_URL = \\"{public_url}\\"\\n")
        print("=" * 60)
        print("\\nThis URL is valid for the current session only")
        print("   (Changes when you restart the notebook)\\n")

    except Exception as e:
        print(f"Ngrok setup failed: {str(e)}\\n")
        print("   Check if auth token is correct")
        print("   Verify internet is enabled in Kaggle settings\\n")
'''
        print(f"Fixed ngrok cell at index {i}")
        break

with open(nb_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1)

print("Done!")
