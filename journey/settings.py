from journey.vendor.dotenv import load_dotenv
import sys
env_path = sys.path.append('./.env')
load_dotenv(dotenv_path=env_path)
