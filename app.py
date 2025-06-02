from flask import Flask, render_template, request, redirect, url_for, session, send_file, jsonify, Response
import csv
import os
from datetime import datetime
import random
from io import StringIO

app = Flask(__name__)
@app.route('/')
def home():
    return 'Bienvenue sur la plateforme Ylema !'
app.secret_key = 'motdepasse-secret-wend'

TICKETS_FILE = 'tickets.csv'
TICKETS_TOTAL = 100
ADMIN_PASSWORD = 'motdepasse'  # change ce mot de passe à ta convenance

# Initialisation du fichier CSV
if not os.path.exists(TICKETS_FILE):
    with open(TICKETS_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Nom', 'Numéro de ticket', 'Téléphone'])

def nombre_tickets_vendus():
    with open(TICKETS_FILE, 'r', encoding='utf-8') as f:
        return sum(1 for row in csv.reader(f)) - 1  # exclure l’en-tête

@app.route('/')
def index():
    tickets_vendus = nombre_tickets_vendus()
    tickets_restants = TICKETS_TOTAL - tickets_vendus
    return render_template('index.html',
                           tickets_total=TICKETS_TOTAL,
                           tickets_vendus=tickets_vendus,
                           tickets_restants=tickets_restants)

@app.route('/payer', methods=['POST'])
def payer():
    nom = request.form['nom']
    telephone = request.form['telephone']
    numero_ticket = random.randint(100000, 999999)

    with open('tickets.csv', mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([nom, numero_ticket, telephone])

    message_confirmation = f"Merci pour votre participation, {nom} ! Votre numéro de ticket est : {numero_ticket}."
    return render_template('confirmation.html', message=message_confirmation)

@app.route('/confirmation')
def confirmation():
    return render_template('confirmation.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form['password']
        if password == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin_login.html', erreur='Mot de passe incorrect')
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    with open(TICKETS_FILE, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        participants = list(reader)[1:]  # on ignore l'en-tête
    tickets_vendus = len(participants)
    tickets_restants = TICKETS_TOTAL - tickets_vendus
    return render_template('admin.html',
                           participants=participants,
                           tickets_vendus=tickets_vendus,
                           tickets_restants=tickets_restants)

@app.route('/admin/telecharger')
def telecharger():
    return send_file(TICKETS_FILE, as_attachment=True)

@app.route('/admin/supprimer/<int:index>')
def supprimer(index):
    with open(TICKETS_FILE, 'r', encoding='utf-8') as f:
        lignes = list(csv.reader(f))
    if index + 1 < len(lignes):
        del lignes[index + 1]  # +1 pour ignorer l'en-tête
        with open(TICKETS_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(lignes)
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/reset')
def reset():
    with open(TICKETS_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Nom', 'Numéro de ticket', 'Téléphone'])
    return redirect(url_for('admin_dashboard'))

@app.route('/tirage', methods=['POST'])
def tirage():
    participants = lire_participants()

    if len(participants) < tickets_total:
        flash("Tous les tickets n'ont pas encore été vendus.", "danger")
        return redirect(url_for('admin_dashboard'))

    gagnant = random.choice(participants)
    return render_template("admin.html", gagnant=gagnant, tickets_vendus=len(participants), tickets_restants=tickets_total - len(participants), tickets_total=tickets_total)

@app.route('/gagnant/<nom>/<ticket>')
def gagnant(nom, ticket):
    return render_template('gagnant.html', nom=nom, ticket=ticket)

@app.route('/telecharger_participants')
def telecharger_participants():
    if not os.path.exists(TICKETS_FILE):
        return "Aucun participant trouvé."

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Nom', 'Numéro de ticket', 'Téléphone'])

    with open(TICKETS_FILE, 'r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)  # Sauter l’en-tête
        for row in reader:
            writer.writerow(row)

    output.seek(0)
    return Response(
        output,
        mimetype='text/csv',
        headers={"Content-Disposition": "attachment;filename=liste_participants.csv"}
    )

if __name__ == '__main__':
    app.run(debug=True)