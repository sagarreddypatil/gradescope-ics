import os
import json
import base64
import dotenv
dotenv.load_dotenv()

if __name__ == "__main__":
    email = os.environ.get("GS_EMAIL")
    pwd = os.environ.get("GS_PWD")
    sem = os.environ.get("GS_SEM")

    # Login
    if email is None:
        email = input("Email: ")
    if pwd is None:
        pwd = input("Password: ")
    if sem is None:
        sem = input("Semester: ")

    json_data = {
        "email": email,
        "pwd": pwd,
        "sem": sem
    }

    json_str = json.dumps(json_data)
    encoded = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')

    print(encoded)
