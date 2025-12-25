from app import create_app, db
from app.models import User, Ticket, Comment, Attachment
from flask_login import login_required, current_user
from flask import (
    render_template,
    request,
    redirect,
    url_for,
    Response,
    jsonify,
    send_from_directory
)
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy import func
import os

app = create_app()

# ---------------- FILE UPLOAD CONFIG ----------------
UPLOAD_FOLDER = "app/uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "pdf", "txt"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return "." in filename and \
           filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ---------------- CREATE TABLES ----------------
with app.app_context():
    db.create_all()


# ---------------- USER DASHBOARD ----------------
@app.route("/dashboard")
@login_required
def dashboard():
    tickets = Ticket.query.filter_by(created_by=current_user.id).all()
    return render_template("dashboard.html", tickets=tickets)


# ---------------- CREATE TICKET (WITH ATTACHMENT) ----------------
@app.route("/create-ticket", methods=["GET", "POST"])
@login_required
def create_ticket():
    if request.method == "POST":
        ticket = Ticket(
            subject=request.form["subject"],
            description=request.form["description"],
            priority=request.form["priority"],
            created_by=current_user.id
        )
        db.session.add(ticket)
        db.session.commit()

        file = request.files.get("attachment")

        # ✅ FIXED FILE CHECK
        if file and file.filename != "" and allowed_file(file.filename):
            filename = secure_filename(file.filename)

            ticket_folder = os.path.join(
                app.config["UPLOAD_FOLDER"], f"ticket_{ticket.id}"
            )
            os.makedirs(ticket_folder, exist_ok=True)

            file.save(os.path.join(ticket_folder, filename))

            attachment = Attachment(
                filename=filename,
                ticket_id=ticket.id
            )
            db.session.add(attachment)
            db.session.commit()

        return redirect(url_for("dashboard"))

    return render_template("create_ticket.html")


# ---------------- TICKET DETAILS + COMMENTS ----------------
@app.route("/ticket/<int:ticket_id>", methods=["GET", "POST"])
@login_required
def ticket_detail(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)

    if request.method == "POST":
        comment = Comment(
            ticket_id=ticket.id,
            user_id=current_user.id,
            comment=request.form["comment"]
        )
        db.session.add(comment)
        db.session.commit()

        return redirect(url_for("ticket_detail", ticket_id=ticket.id))

    comments = Comment.query.filter_by(ticket_id=ticket.id).all()
    return render_template("ticket_detail.html", ticket=ticket, comments=comments)


# ---------------- DOWNLOAD ATTACHMENT ----------------
@app.route("/attachment/<int:attachment_id>/download")
@login_required
def download_attachment(attachment_id):
    attachment = Attachment.query.get_or_404(attachment_id)
    ticket = attachment.ticket

    if current_user.role not in ["ADMIN", "AGENT"] and ticket.created_by != current_user.id:
        return "Access Denied", 403

    folder = os.path.join(app.config["UPLOAD_FOLDER"], f"ticket_{ticket.id}")

    return send_from_directory(
        directory=folder,
        path=attachment.filename,
        as_attachment=True
    )


# ---------------- CHANGE TICKET STATUS ----------------
@app.route("/ticket/<int:ticket_id>/status/<status>")
@login_required
def change_status(ticket_id, status):
    ticket = Ticket.query.get_or_404(ticket_id)
    ticket.status = status
    db.session.commit()
    return redirect(url_for("ticket_detail", ticket_id=ticket.id))


# ---------------- ADMIN PANEL (WITH PAGINATION) ----------------
@app.route("/admin")
@login_required
def admin_panel():
    if current_user.role != "ADMIN":
        return "Access Denied", 403

    page = request.args.get("page", 1, type=int)
    PER_PAGE = 5

    users = User.query.all()
    tickets = Ticket.query.order_by(Ticket.id.desc()).paginate(
        page=page,
        per_page=PER_PAGE,
        error_out=False
    )

    return render_template("admin.html", users=users, tickets=tickets)


# ---------------- CHANGE USER ROLE ----------------
@app.route("/admin/user/<int:user_id>/role/<role>")
@login_required
def change_user_role(user_id, role):
    if current_user.role != "ADMIN":
        return "Access Denied", 403

    user = User.query.get_or_404(user_id)
    user.role = role
    db.session.commit()
    return redirect(url_for("admin_panel"))


# ---------------- ADD AGENT ----------------
@app.route("/admin/add-agent", methods=["GET", "POST"])
@login_required
def add_agent():
    if current_user.role != "ADMIN":
        return "Access Denied", 403

    if request.method == "POST":
        agent = User(
            name=request.form["name"],
            email=request.form["email"],
            password=generate_password_hash(request.form["password"]),
            role="AGENT"
        )
        db.session.add(agent)
        db.session.commit()
        return redirect(url_for("admin_panel"))

    return render_template("add_agent.html")


# ---------------- ASSIGN TICKET ----------------
@app.route("/admin/ticket/<int:ticket_id>/assign", methods=["POST"])
@login_required
def assign_ticket(ticket_id):
    if current_user.role != "ADMIN":
        return "Access Denied", 403

    ticket = Ticket.query.get_or_404(ticket_id)
    ticket.assigned_to = request.form["agent_id"]
    ticket.status = "IN_PROGRESS"
    db.session.commit()

    return redirect(url_for("admin_panel"))


# ---------------- AGENT DASHBOARD ----------------
@app.route("/agent/dashboard")
@login_required
def agent_dashboard():
    if current_user.role != "AGENT":
        return "Access Denied", 403

    tickets = Ticket.query.filter_by(assigned_to=current_user.id).all()
    return render_template("agent_dashboard.html", tickets=tickets)


# ---------------- AGENT ESCALATE ----------------
@app.route("/agent/ticket/<int:ticket_id>/escalate")
@login_required
def escalate_ticket(ticket_id):
    if current_user.role != "AGENT":
        return "Access Denied", 403

    ticket = Ticket.query.get_or_404(ticket_id)

    if ticket.assigned_to != current_user.id:
        return "Not your ticket", 403

    ticket.status = "ESCALATED"
    ticket.assigned_to = None
    db.session.commit()

    return redirect(url_for("agent_dashboard"))


# ---------------- ADMIN TAKE ESCALATED ----------------
@app.route("/admin/ticket/<int:ticket_id>/take")
@login_required
def admin_take_ticket(ticket_id):
    if current_user.role != "ADMIN":
        return "Access Denied", 403

    ticket = Ticket.query.get_or_404(ticket_id)
    ticket.assigned_to = current_user.id
    ticket.status = "IN_PROGRESS"
    db.session.commit()

    return redirect(url_for("admin_panel"))


# ---------------- EXPORT CSV (FIXED) ----------------
@app.route("/admin/export")
@login_required
def export_tickets_csv():
    if current_user.role != "ADMIN":
        return "Access Denied", 403

    tickets = Ticket.query.all()

    if not tickets:
        return "No tickets to export", 404

    import io
    import csv

    output = io.StringIO()
    writer = csv.writer(output)

    # CSV HEADER
    writer.writerow([
        "ID",
        "Subject",
        "Status",
        "Priority",
        "Assigned To",
        "Created By"
    ])

    # CSV ROWS
    for t in tickets:
        writer.writerow([
            t.id,
            t.subject,
            t.status,
            t.priority,
            t.assignee.name if t.assigned_to else "",
            t.creator.name
        ])

    output.seek(0)

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=tickets_export.csv"
        }
    )


# ---------------- ADMIN CHART DATA ----------------
@app.route("/admin/charts/data")
@login_required
def admin_charts_data():
    if current_user.role != "ADMIN":
        return "Access Denied", 403

    return jsonify({
        "status": dict(db.session.query(Ticket.status, func.count()).group_by(Ticket.status)),
        "priority": dict(db.session.query(Ticket.priority, func.count()).group_by(Ticket.priority)),
        "agent": dict(
            db.session.query(User.name, func.count())
            .join(Ticket, Ticket.assigned_to == User.id)
            .group_by(User.name)
        )
    })

@app.route("/ticket/<int:ticket_id>/rate", methods=["POST"])
@login_required
def rate_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)

    # Only ticket creator can rate
    if ticket.created_by != current_user.id:
        return "Access Denied", 403

    # Only resolved or closed tickets can be rated
    if ticket.status not in ["RESOLVED", "CLOSED"]:
        return "Ticket not resolved yet", 400

    ticket.rating = int(request.form["rating"])
    ticket.feedback = request.form.get("feedback")

    db.session.commit()
    return redirect(url_for("ticket_detail", ticket_id=ticket.id))

# ---------------- HOME ----------------
@app.route("/")
def home():
    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    app.run()