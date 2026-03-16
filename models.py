from database import db

class Transaction(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  description = db.Column(db.String(100), nullable=False)
  amount = db.Column(db.Float, nullable=False)
  category = db.Column(db.String(50), nullable=False)
  type = db.Column(db.String(20), nullable=False)
  date = db.Column(db.String(10), nullable=False)

  def __repr__(self):
    return f"<Transaction {self.description}>"
  
class User(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(100), nullable=False)
  email = db.Column(db.String(120), unique=True, nullable=False)
  password_hash = db.Column(db.String(255), nullable=False)

  def __repr__(self):
      return f"<User {self.email}>"