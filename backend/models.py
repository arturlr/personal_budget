from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import hashlib

db = SQLAlchemy()

class Account(db.Model):
    __tablename__ = 'accounts'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    number = db.Column(db.String(50))
    ofx_account_id = db.Column(db.String(100))
    starting_balance = db.Column(db.Numeric(10, 2), default=0)
    starting_balance_date = db.Column(db.Date)
    
    transactions = db.relationship('Transaction', back_populates='account', cascade='all, delete-orphan')

class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    type = db.Column(db.String(20), nullable=False)  # income | expense | transfer
    color = db.Column(db.String(20))
    
    parent = db.relationship('Category', remote_side=[id], backref='subcategories')

class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    memo = db.Column(db.Text)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    subcategory_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    suggested_category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    suggested_subcategory_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    is_approved = db.Column(db.Boolean, default=False)
    is_credit_card_payment = db.Column(db.Boolean, default=False)
    accrual_start_date = db.Column(db.Date)
    accrual_end_date = db.Column(db.Date)
    accrual_method = db.Column(db.String(20))
    unique_hash = db.Column(db.String(64), unique=True, nullable=False)
    
    account = db.relationship('Account', back_populates='transactions')
    category = db.relationship('Category', foreign_keys=[category_id])
    subcategory = db.relationship('Category', foreign_keys=[subcategory_id])
    suggested_category = db.relationship('Category', foreign_keys=[suggested_category_id])
    suggested_subcategory = db.relationship('Category', foreign_keys=[suggested_subcategory_id])
    
    @staticmethod
    def generate_hash(account_id, date, memo, amount):
        data = f"{account_id}|{date}|{memo}|{amount}"
        return hashlib.sha256(data.encode()).hexdigest()

class CategoryRule(db.Model):
    __tablename__ = 'category_rules'
    
    id = db.Column(db.Integer, primary_key=True)
    pattern = db.Column(db.Text, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    subcategory_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    priority = db.Column(db.Integer, default=0)
    
    category = db.relationship('Category', foreign_keys=[category_id])
    subcategory = db.relationship('Category', foreign_keys=[subcategory_id])

class ForecastItem(db.Model):
    __tablename__ = 'forecast_items'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    subcategory_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    frequency = db.Column(db.String(20), nullable=False)  # monthly | annual | quarterly
    type = db.Column(db.String(20), nullable=False)  # fixed | variable
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)
    
    category = db.relationship('Category', foreign_keys=[category_id])
    subcategory = db.relationship('Category', foreign_keys=[subcategory_id])
