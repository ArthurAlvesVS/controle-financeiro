from flask import Flask, render_template
from database import db
from models import Transaction
app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///finance.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

@app.route("/")
def home():
  return render_template("index.html")

if __name__ == "__main__":
  with app.app_context():
      db.create_all()
  app.run(debug=True)