import os
from datetime import datetime

from flask import Flask, abort, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_serializer import SerializerMixin

db = SQLAlchemy()
app = Flask(__name__)
app.debug = True
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DB_URL']
db.init_app(app)


class BaseModel(db.Model, SerializerMixin):
    __abstract__ = True


class Category(BaseModel):
    __tablename__ = 'categories'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    created_on = db.Column(db.DateTime(), default=datetime.utcnow)

    def __repr__(self):
        return f"category:{self.id}:{self.name}"


class Entry(BaseModel):
    __tablename__ = 'entries'
    id = db.Column(db.Integer(), primary_key=True)
    created_on = db.Column(db.DateTime(), default=datetime.utcnow)

    items = db.relationship('EntryItem')

    def __repr__(self):
        return f"entry:{self.id}"


class EntryItem(BaseModel):
    __tablename__ = 'entry_items'
    id = db.Column(db.Integer(), primary_key=True)
    portion = db.Column(db.Integer())
    created_on = db.Column(db.DateTime(), default=datetime.utcnow)
    updated_on = db.Column(db.DateTime(), default=datetime.utcnow)

    entry_id = db.Column(db.Integer(), db.ForeignKey('entries.id'))
    category_id = db.Column(db.Integer())
    # category_id = db.Column(db.Integer(), db.ForeignKey('categories.id'))

    def __repr__(self):
        return f"entry_item:{self.id}:{self.entry_id}:{self.portion}"


food_categories = [
    'Wheat',
    'Meat',
    'Veggie',
    'Fruit',
    'Alcohol',
    'Beverage',
    'Milk',
    'Cheese',
    'Beans',
    'Nuts'
]

with app.app_context():
    db_file_path = "my_db.db"
    if os.path.exists(db_file_path):
        os.remove(db_file_path)
    db.create_all()
    cats = []
    for food in food_categories:
        cat = Category(name=food)
        cats.append(cat)

    db.session.add_all(cats)
    db.session.commit()


@app.route('/api/categories/')
def categories():
    cats = db.session.query(Category).all()
    return jsonify([cat.to_dict() for cat in cats])


@app.route('/api/track/', methods=['POST'])
def track():
    tracking_record = Entry()

    items = request.json.get('foods', [])
    for item in items:
        item_record = EntryItem(
            portion=item['portion'], category_id=item['category'])
        tracking_record.items.append(item_record)

    db.session.add(tracking_record)
    db.session.commit()

    return tracking_record.to_dict()


@app.route('/api/track/<id>/', methods=['PUT'])
def update_track(id):
    res = db.session.query(Entry).get(id)
    if not res:
        return abort(404)
    items = request.json.get('foods', [])
    entry_item_category_ids = []
    new_entry_items = []
    for item in items:
        entry_item_category_ids.append(item['category'])
        new_item = EntryItem(
            portion=item['portion'], category_id=item['category'])
        new_entry_items.append(new_item)

    items_to_delete = EntryItem.query.filter(
        EntryItem.category_id.in_(entry_item_category_ids)).filter(EntryItem.entry_id == res.id)
    items_to_delete.delete()
    res.items.extend(new_entry_items)
    db.session.commit()
    return res.to_dict()


if __name__ == "__main__":
    app.run()
