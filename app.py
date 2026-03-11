from flask import Flask, render_template, request, redirect, url_for
from database import db
from models import Transaction

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///finance.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

@app.route("/")
def home():
  return render_template("index.html")

@app.route("/add", methods=["GET", "POST"])
def add_transaction():
   if request.method == "POST":
      description = request.form["description"]
      amount = float(request.form["amount"])
      category = request.form["category"]
      transaction_type = request.form["type"]

      new_transaction = Transaction(
         description=description,
         amount=amount,
         category=category,
         type=transaction_type
      )

      db.session.add(new_transaction)
      db.session.commit()

      return redirect(url_for("home"))
   
   return render_template("add_transaction.html")

if __name__ == "__main__":
  with app.app_context():
      db.create_all()
  app.run(debug=True)