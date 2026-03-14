import csv
import io
from io import BytesIO
from flask import Flask, render_template, request, redirect, url_for, flash, Response
from openpyxl import Workbook
from database import db
from models import Transaction

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///finance.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "minha_chave_secreta"

db.init_app(app)

def get_filtered_transactions():
    sort = request.args.get("sort", "date")
    order = request.args.get("order", "desc")
    month = request.args.get("month")
    year = request.args.get("year")
    search = request.args.get("search", "").strip().lower()

    transactions = Transaction.query.all()

    if month and year:
        transactions = [
            t for t in transactions
            if t.date.startswith(f"{year}-{month}")
        ]

    if search:
        transactions = [
            t for t in transactions
            if search in t.description.lower() or search in t.category.lower()
        ]

    if sort == "date":
        transactions = sorted(
            transactions,
            key=lambda t: t.date,
            reverse=(order == "desc")
        )
    elif sort == "amount":
        transactions = sorted(
            transactions,
            key=lambda t: t.amount,
            reverse=(order == "desc")
        )
    elif sort == "category":
        transactions = sorted(
            transactions,
            key=lambda t: t.category.lower(),
            reverse=(order == "desc")
        )

    return transactions, sort, order, month, year, search

@app.route("/")
def home():
    transactions, sort, order, month, year, search = get_filtered_transactions()

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
        selected_year=year,
        selected_sort=sort,
        selected_order=order,
        search_term=search
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

      flash("Transação adicionada com sucesso.", "success")

      return redirect(url_for("home"))
   
   return render_template("add_transaction.html")

@app.route("/delete/<int:id>")
def delete_transaction(id):
   transaction = Transaction.query.get_or_404(id)

   db.session.delete(transaction)
   db.session.commit()

   flash("Transação excluída com sucesso.", "success")

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

@app.route("/export/csv")
def export_csv():
   transactions, _, _, _, _, _ = get_filtered_transactions()

   output = io.StringIO()
   writer = csv.writer(output)

   writer.writerow(["Descrição", "Valor", "Categoria", "Tipo", "Data"])

   for transaction in transactions:
      writer.writerow([
         transaction.description,
         transaction.amount,
         transaction.category,
         transaction.type,
         transaction.date
      ])

   csv_data = output.getvalue()
   output.close()

   return Response(
      csv_data,
      mimetype="text/csv",
      headers={"Content-Disposition": "attachment; filename=transacoes.csv"}
   )

@app.route("/export/excel")
def export_excel():
   transactions, _, _, _, _, _ = get_filtered_transactions()

   workbook = Workbook()
   sheet = workbook.active
   sheet.title = "Transações"

   sheet.append(["Descrição", "Valor", "Categoria", "Tipo", "Data"])

   for transaction in transactions:
      sheet.append([
         transaction.description,
         transaction.amount,
         transaction.category,
         transaction.type,
         transaction.date
      ])

   output = BytesIO()
   workbook.save(output)
   output.seek(0)

   return Response(
      output.getvalue(),
      mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      headers={"Content-Disposition": "attachment; filename=transacoes.xlsx"}
   )

@app.template_filter("currency")
def currency_format(value):
    return "R$ " + "{:,.2f}".format(value).replace(",", "X").replace(".", ",").replace("X", ".")

if __name__ == "__main__":
  with app.app_context():
      db.create_all()
  app.run(debug=True)