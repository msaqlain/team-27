
## Prerequisites
- Python 3.10 (recommended)
- pip package manager
- OpenAI API key
- Dapr CLI and Docker installed

## Environment Setup

```bash
# Create a virtual environment
python3.10 -m venv .venv

# Activate the virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

dapr init 

dapr run -f dapr.yaml

```

open http://localhost:3000/ for frontend.

open http://localhost:8000/api/v1/health for backend.


Test
