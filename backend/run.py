import os
from dotenv import load_dotenv

# Load environment variables FIRST (before any other imports)
load_dotenv()

# Set Hugging Face cache from .env or use default
hf_home = os.getenv('HF_HOME', os.path.join(os.path.dirname(__file__), '.cache'))
os.environ['HF_HOME'] = hf_home

# Get compute device from .env
compute_device = os.getenv('COMPUTE_DEVICE', 'cuda').lower()
if compute_device not in ['cuda', 'cpu']:
    compute_device = 'cuda'
os.environ['COMPUTE_DEVICE'] = compute_device

# Configure TensorFlow to allow GPU memory growth BEFORE importing TF
if compute_device == 'cuda':
    os.environ['TF_FORCE_GPU_ALLOW_GROWTH'] = 'true'
    print(f"Using COMPUTE_DEVICE: {compute_device} (GPU with memory growth enabled)")
else:
    print(f" Using COMPUTE_DEVICE: {compute_device} (CPU only)")

# Clear GPU memory if using GPU
if compute_device == 'cuda':
    try:
        import torch
        print(" Clearing GPU memory at startup...")
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats()
        print("GPU memory cleared")
    except Exception as e:
        print(f"Note: GPU clearing not available: {e}")



from app import create_app
from database import db_setup

app = create_app()


if __name__ == "__main__":
    db_setup.init_db(app)
    app.run(host="0.0.0.0", port=5000, debug=True)
