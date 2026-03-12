from flask import Flask, render_template, request, redirect, url_for
from database import db
from models import Transaction

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///finance.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

@app.route("/")
def home():
    month = request.args.get("month")
    year = request.args.get("year")

    transactions = Transaction.query.all()

    if month and year:
       transactions = [
          t for t in transactions
          if t.date.statswith(f"{year}-{month}")
       ]

    total_receitas = sum(t.amount for t in transactions if t.type == "receita")
    total_despesas = sum(t.amount for t in transactions if t.type == "despesa")
    saldo = total_receitas - total_despesas

    despesas_por_categoria = {}

    for t in transactions:
         if t.type == "despesa":
            if t.category in despesas_por_categoria:
             despesas_por_categoria[t.category] += t.amount
            else:
               despesas_por_categoria[t.category] = t.amount
        
    categorias = list(despesas_por_categoria.keys())
    valores = list(despesas_por_categoria.values())
    
    return render_template(
         "index.html", 
         transactions=transactions,
         total_receitas=total_receitas,
         total_despesas=total_despesas,
         saldo=saldo,
         categorias=categorias,
         valores=valores,
         selected_month=month,
         selected_year=year
      )

@app.route("/add", methods=["GET", "POST"])
def add_transaction():
   if request.method == "POST":
      description = request.form["description"]
      amount = float(request.form["amount"])
      category = request.form["category"]
      transaction_type = request.form["type"]
      date = request.form["date"]

      new_transaction = Transaction(
         description=description,
         amount=amount,
         category=category,
         type=transaction_type,
         date=date
      )

      db.session.add(new_transaction)
      db.session.commit()

      return redirect(url_for("home"))
   
   return render_template("add_transaction.html")

@app.route("/delete/<int:id>")
def delete_transaction(id):
   transaction = Transaction.query.get_or_404(id)

   db.session.delete(transaction)
   db.session.commit()

   return redirect(url_for("home"))

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_transaction(id):
    transaction = Transaction.query.get_or_404(id)

    if request.method == "POST":
        transaction.description = request.form["description"]
        transaction.amount = float(request.form["amount"])
        transaction.category = request.form["category"]
        transaction.type = request.form["type"]
        transaction.date = request.form["date"]

        db.session.commit()

        return redirect(url_for("home"))

    return render_template("edit_transaction.html", transaction=transaction)

if __name__ == "__main__":
  with app.app_context():
      db.create_all()
  app.run(debug=True)