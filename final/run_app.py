import webbrowser
from threading import Timer
from app import app  # your Flask app

# Automatically open browser after a short delay
def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000/")

# Launch browser after 1 second
Timer(1, open_browser).start()

# Run Flask app
app.run(debug=False, use_reloader=False)
