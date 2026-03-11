from database import db

class Transaction(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  description = db.Column(db.String(100), nullable=False)
  amount = db.Column(db.Float, nullable=False)
  category = db.Column(db.String(50), nullable=False)
  type = db.Column(db.String(20), nullable=False)

  def __repr__(self):
    return f"<Transaction {self.description}>"