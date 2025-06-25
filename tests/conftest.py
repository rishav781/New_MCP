import os
from dotenv import load_dotenv

# Load .env file before any tests run
def pytest_configure(config):
    # Load .env file and map PLOUDY_* to PCLOUDY_*
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    load_dotenv(dotenv_path=env_path, override=True)
    if os.environ.get('PLOUDY_USERNAME'):
        os.environ['PCLOUDY_USERNAME'] = os.environ['PLOUDY_USERNAME']
    if os.environ.get('PLOUDY_API_KEY'):
        os.environ['PCLOUDY_API_KEY'] = os.environ['PLOUDY_API_KEY']
