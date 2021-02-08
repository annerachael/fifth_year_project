# server.py

from app import create_app

"""
This module shall be the starting up of the web app
"""


app = create_app()

# route different pages
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
