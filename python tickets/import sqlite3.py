import sqlite3
import qrcode
import uuid
from datetime import datetime
from PIL import Image  # Ensure Pillow is installed
from flask import Flask, request, render_template, redirect, url_for

app = Flask(__name__)

# Database setup
def init_db():
    conn = sqlite3.connect("tickets.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS tickets (
                        id TEXT PRIMARY KEY,
                        buyer_name TEXT,
                        ticket_type TEXT,
                        qr_code TEXT UNIQUE,
                        checked_in INTEGER DEFAULT 0
                      )''')
    conn.commit()
    conn.close()

# Generate a unique QR code for a ticket
def generate_qr_code(ticket_id):
    qr = qrcode.make(ticket_id)
    qr_image_path = f"static/{ticket_id}.png"
    qr.save(qr_image_path)
    return qr_image_path

# Purchase a ticket
@app.route("/purchase", methods=["GET", "POST"])
def purchase_ticket():
    if request.method == "POST":
        buyer_name = request.form["buyer_name"]
        ticket_type = request.form["ticket_type"]
        ticket_id = str(uuid.uuid4())[:8]
        conn = sqlite3.connect("tickets.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO tickets (id, buyer_name, ticket_type, qr_code) VALUES (?, ?, ?, ?)",
                       (ticket_id, buyer_name, ticket_type, ticket_id))
        conn.commit()
        conn.close()
        qr_code_path = generate_qr_code(ticket_id)
        return render_template("purchase_success.html", qr_code_path=qr_code_path, ticket_id=ticket_id)
    return render_template("purchase.html")

# Check-in system
@app.route("/checkin", methods=["GET", "POST"])
def check_in():
    if request.method == "POST":
        qr_code = request.form["qr_code"]
        conn = sqlite3.connect("tickets.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tickets WHERE qr_code = ?", (qr_code,))
        ticket = cursor.fetchone()
        
        if not ticket:
            return "Invalid QR code. Access denied!"
        elif ticket[4] == 1:  # Checked-in status
            return "Fraud detected! Ticket already used."
        else:
            cursor.execute("UPDATE tickets SET checked_in = 1 WHERE qr_code = ?", (qr_code,))
            conn.commit()
            conn.close()
            return f"Welcome, {ticket[1]}! Enjoy the event."
    return render_template("checkin.html")

# Display summary report
@app.route("/summary")
def show_summary():
    conn = sqlite3.connect("tickets.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM tickets")
    total_tickets = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM tickets WHERE checked_in = 1")
    checked_in_tickets = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM tickets WHERE checked_in = 0")
    not_checked_in = cursor.fetchone()[0]
    conn.close()
    return render_template("summary.html", total_tickets=total_tickets, checked_in_tickets=checked_in_tickets, not_checked_in=not_checked_in)

# Initialize database
init_db()

if __name__ == "__main__":
    app.run(debug=True)
