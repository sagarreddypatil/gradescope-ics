from main import do_the_thing
from flask import Flask, request, send_file, render_template, make_response
import json
import base64
from typing import Dict, Any
from io import BytesIO

app = Flask(__name__)


@app.route("/")
def index():
    response = make_response(render_template("index.html"))
    response.headers["Cache-Control"] = "public, max-age=3600"

    return response


@app.route("/gradescope.ics")
def gradescope_calendar():
    try:
        # Get the base64 encoded query parameter
        encoded_data = request.args.get("data")
        if not encoded_data:
            return "Missing data parameter", 400

        # Decode base64 to JSON string
        try:
            json_str = base64.b64decode(encoded_data).decode("utf-8")
        except Exception as e:
            return f"Invalid base64 encoding: {str(e)}", 400

        # Parse JSON
        try:
            data: Dict[str, Any] = json.loads(json_str)
        except json.JSONDecodeError as e:
            return f"Invalid JSON: {str(e)}", 400

        # Validate required fields
        required_fields = ["email", "pwd", "sem"]
        for field in required_fields:
            if field not in data:
                return f"Missing required field: {field}", 400

        # Call do_the_thing with the parameters
        file_data = do_the_thing(email=data["email"], pwd=data["pwd"], sem=data["sem"])

        file_str = "".join(file_data)
        file_io = BytesIO(file_str.encode("utf-8"))

        # Send the file
        return send_file(
            file_io,
            mimetype="text/calendar",
            as_attachment=True,
            download_name="gradescope.ics",
        )

    except Exception as e:
        return f"Server error: {str(e)}", 500


if __name__ == "__main__":
    app.run(debug=True)
