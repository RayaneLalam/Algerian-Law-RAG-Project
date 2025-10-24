from app import create_app
from database import db_setup

app = create_app()

if __name__ == "__main__":
    db_setup.init_db(app)
    app.run(host="0.0.0.0", port=5000, debug=True)
