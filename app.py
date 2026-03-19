import csv
import io
from io import BytesIO
from flask import Flask, render_template, request, redirect, url_for, flash, Response,session
from werkzeug.security import generate_password_hash, check_password_hash
from openpyxl import Workbook
from database import db
from models import Transaction, User
from auth_utils import login_required

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///finance.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "minha_chave_secreta"

db.init_app(app)

def get_user_transactions_query():
    return Transaction.query.filter_by(user_id=session["user_id"])

def get_current_user_id():
    return session.get("user_id")

def get_filtered_transactions():
    sort = request.args.get("sort", "date")
    order = request.args.get("order", "desc")
    month = request.args.get("month")
    year = request.args.get("year")
    search = request.args.get("search", "").strip().lower()

    transactions = get_user_transactions_query().all()

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

def generate_insights(transactions, total_receitas, total_despesas, saldo, despesas_por_categoria):
    insights = []

    if not transactions:
        insights.append("Você ainda não possui transações cadastradas.")
        return insights

    if total_despesas > total_receitas:
        insights.append("Suas despesas estão maiores que suas receitas.")
    elif total_receitas > total_despesas:
        insights.append("Suas receitas estão maiores que suas despesas.")
    else:
        insights.append("Suas receitas e despesas estão no mesmo valor.")

    if saldo > 0:
        insights.append("Seu saldo atual está positivo.")
    elif saldo < 0:
        insights.append("Seu saldo atual está negativo.")
    else:
        insights.append("Seu saldo atual está zerado.")

    if despesas_por_categoria:
        maior_categoria = max(despesas_por_categoria, key=despesas_por_categoria.get)
        maior_valor = despesas_por_categoria[maior_categoria]
        valor_formatado = "{:,.2f}".format(maior_valor).replace(",", "X").replace(".", ",").replace("X", ".")
        insights.append(
            f"Sua maior categoria de despesa é {maior_categoria}, com total de R$ {valor_formatado}."
        )

    total_transacoes = len(transactions)
    insights.append(f"Você possui {total_transacoes} transações no período analisado.")

    return insights

def compare_with_previous_month(transactions):
    from datetime import datetime

    if not transactions:
        return []

    comparacoes = []

    hoje = datetime.today()
    mes_atual = hoje.strftime("%Y-%m")
    
    if hoje.month == 1:
        mes_anterior = f"{hoje.year - 1}-12"
    else:
        mes_anterior = f"{hoje.year}-{str(hoje.month - 1).zfill(2)}"

    receitas_atual = 0
    despesas_atual = 0
    receitas_anterior = 0
    despesas_anterior = 0

    for t in transactions:
        mes = t.date[:7]

        if mes == mes_atual:
            if t.type == "receita":
                receitas_atual += t.amount
            else:
                despesas_atual += t.amount

        elif mes == mes_anterior:
            if t.type == "receita":
                receitas_anterior += t.amount
            else:
                despesas_anterior += t.amount

    def calcular_variacao(atual, anterior):
        if anterior == 0:
            return None
        return ((atual - anterior) / anterior) * 100

    variacao_receita = calcular_variacao(receitas_atual, receitas_anterior)
    variacao_despesa = calcular_variacao(despesas_atual, despesas_anterior)

    if variacao_receita is not None:
        if variacao_receita > 0:
            comparacoes.append(f"Sua receita aumentou {variacao_receita:.1f}% em relação ao mês anterior.")
        elif variacao_receita < 0:
            comparacoes.append(f"Sua receita diminuiu {abs(variacao_receita):.1f}% em relação ao mês anterior.")

    if variacao_despesa is not None:
        if variacao_despesa > 0:
            comparacoes.append(f"Suas despesas aumentaram {variacao_despesa:.1f}% em relação ao mês anterior.")
        elif variacao_despesa < 0:
            comparacoes.append(f"Suas despesas diminuíram {abs(variacao_despesa):.1f}% em relação ao mês anterior.")

    return comparacoes

def generate_alerts(transactions, total_receitas, total_despesas, saldo, despesas_por_categoria):
    alerts = []

    if not transactions:
        return alerts

    if total_despesas > total_receitas:
        alerts.append("Alerta: suas despesas estão maiores do que suas receitas.")

    if saldo < 0:
        alerts.append("Alerta: seu saldo está negativo.")

    if total_despesas > 0 and despesas_por_categoria:
        maior_categoria = max(despesas_por_categoria, key=despesas_por_categoria.get)
        maior_valor = despesas_por_categoria[maior_categoria]
        percentual = (maior_valor / total_despesas) * 100

        if percentual >= 50:
            alerts.append(
                f"Atenção: {maior_categoria} representa {percentual:.1f}% das suas despesas totais."
            )

    return alerts


@app.route("/")
@login_required
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

    insights = generate_insights(
        transactions,
        total_receitas,
        total_despesas,
        saldo,
        despesas_por_categoria
    )

    comparacoes = compare_with_previous_month(transactions)

    alerts = generate_alerts(
        transactions,
        total_receitas,
        total_despesas,
        saldo,
        despesas_por_categoria
    )

    receitas_por_mes = {}
    despesas_por_mes = {}

    for t in transactions:
        mes = t.date[:7]

        if t.type == "receita":
            if mes in receitas_por_mes:
                receitas_por_mes[mes] += t.amount
            else:
                receitas_por_mes[mes] = t.amount
        
        elif t.type == "despesa":
            if mes in despesas_por_mes:
                despesas_por_mes[mes] += t.amount
            else:
                despesas_por_mes[mes] = t.amount

    todos_os_meses = sorted(set(receitas_por_mes.keys()) | set(despesas_por_mes.keys()))
    receitas_mensais = [receitas_por_mes.get(mes, 0) for mes in todos_os_meses]
    despesas_mensais = [despesas_por_mes.get(mes, 0) for mes in todos_os_meses]

    user = User.query.get_or_404(session["user_id"])
    monthly_goal = user.monthly_goal or 0

    valor_guardado = saldo

    if monthly_goal > 0 and valor_guardado > 0:
        progresso_meta = min((valor_guardado / monthly_goal) * 100, 100)
    else:
        progresso_meta = 0

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
        search_term=search,
        meses=todos_os_meses,
        receitas_mensais=receitas_mensais,
        despesas_mensais=despesas_mensais,
        insights=insights,
        comparacoes=comparacoes,
        alerts=alerts,
        monthly_goal=monthly_goal,
        valor_guardado=valor_guardado,
        progresso_meta=progresso_meta
    )

@app.route("/add", methods=["GET", "POST"])
@login_required
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
         date=date,
         user_id=session["user_id"]
      )

      db.session.add(new_transaction)
      db.session.commit()

      flash("Transação adicionada com sucesso.", "success")

      return redirect(url_for("home"))
   
   return render_template("add_transaction.html")

@app.route("/delete/<int:id>")
@login_required
def delete_transaction(id):
   
   transaction = Transaction.query.filter_by(id=id, user_id=session["user_id"]).first_or_404()

   db.session.delete(transaction)
   db.session.commit()

   flash("Transação excluída com sucesso.", "success")

   return redirect(url_for("home"))

@app.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_transaction(id):

    transaction = Transaction.query.filter_by(id=id, user_id=session["user_id"]).first_or_404()

    if request.method == "POST":
        transaction.description = request.form["description"]
        transaction.amount = float(request.form["amount"])
        transaction.category = request.form["category"]
        transaction.type = request.form["type"]
        transaction.date = request.form["date"]

        db.session.commit()

        flash("Transação atualizada com sucesso.", "success")

        return redirect(url_for("home"))

    return render_template("edit_transaction.html", transaction=transaction)

@app.route("/export/csv")
@login_required
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
@login_required
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

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":

        first_name = request.form["first_name"].strip()
        last_name = request.form["last_name"].strip()
        phone = request.form["phone"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            flash("Já existe um usuário com esse e-mail.", "error")
            return redirect(url_for("register"))

        password_hash = generate_password_hash(password)

        new_user = User(
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            email=email,
            password_hash=password_hash
        )

        db.session.add(new_user)
        db.session.commit()

        flash("Cadastro realizado com sucesso. Faça login para continuar.", "success")
        return redirect(url_for("login"))
    
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":

        email = request.form["email"].strip().lower()
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            session["user_id"] = user.id
            session["user_name"] = user.full_name()

            flash("Login realizado com sucesso.", "success")
            return redirect(url_for("home"))
        
        flash("E-mail ou senha inválidos.", "error")
        return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Você saiu da conta com sucesso.", "success")
    return redirect(url_for("login"))

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():    
    user = User.query.get_or_404(session["user_id"])

    if request.method == "POST":
        first_name = request.form["first_name"].strip()
        last_name = request.form["last_name"].strip()
        phone = request.form["phone"].strip()
        monthly_goal = float(request.form["monthly_goal"] or 0)

        if not first_name or not last_name or not phone:
            flash("Preencha todos os campos obrigatórios.", "error")
            return redirect(url_for("profile"))
        
        user.first_name = first_name
        user.last_name = last_name
        user.phone = phone
        user.monthly_goal = monthly_goal
        db.session.commit()

        session["user_name"] = user.full_name()

        flash("Perfil atualizado com sucesso.", "success")
        return redirect(url_for("profile"))

    return render_template("profile.html", user=user)

if __name__ == "__main__":
  with app.app_context():
      db.create_all()

  print(app.url_map)
  app.run(debug=True)