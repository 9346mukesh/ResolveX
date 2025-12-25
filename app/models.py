from app import db
from flask_login import UserMixin
from datetime import datetime


# ================= USER =================
class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(10), default="USER")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    tickets_created = db.relationship(
        "Ticket",
        foreign_keys="Ticket.created_by",
        backref="creator",
        lazy=True
    )

    tickets_assigned = db.relationship(
        "Ticket",
        foreign_keys="Ticket.assigned_to",
        backref="assignee",
        lazy=True
    )


# ================= TICKET =================
class Ticket(db.Model):
    __tablename__ = "tickets"

    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(10), default="LOW")
    status = db.Column(db.String(20), default="OPEN")

    # ⭐ RATING FEATURE (NEW)
    rating = db.Column(db.Integer, nullable=True)     # 1–5 stars
    feedback = db.Column(db.Text, nullable=True)      # optional user feedback

    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    assigned_to = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    comments = db.relationship(
        "Comment",
        backref="ticket",
        lazy=True
    )

    attachments = db.relationship(
        "Attachment",
        backref="ticket",
        lazy=True
    )


# ================= COMMENT =================
class Comment(db.Model):
    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey("tickets.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    comment = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ================= ATTACHMENT =================
class Attachment(db.Model):
    __tablename__ = "attachments"

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    ticket_id = db.Column(db.Integer, db.ForeignKey("tickets.id"), nullable=False)