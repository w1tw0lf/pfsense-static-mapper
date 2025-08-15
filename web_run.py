import subprocess

if __name__ == '__main__':
    subprocess.call(['gunicorn', '--bind', '0.0.0.0:8000', 'wsgi:app'])