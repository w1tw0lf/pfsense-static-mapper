import argparse
from werkzeug.security import generate_password_hash

parser = argparse.ArgumentParser(description='Hash a password.')
parser.add_argument('password', type=str, help='The password to hash.')
args = parser.parse_args()

print(generate_password_hash(args.password))