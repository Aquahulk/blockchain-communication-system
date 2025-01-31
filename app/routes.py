from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User, Message
from app.blockchain import create_genesis_block, create_new_block
from app import db

main = Blueprint('main', __name__)

# Initialize blockchain
blockchain = [create_genesis_block()]

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please log in.')
        return redirect(url_for('main.login'))
    return render_template('register.html')

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid username or password.')
    return render_template('login.html')

@main.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', username=current_user.username)

@main.route('/send_message', methods=['GET', 'POST'])
@login_required
def send_message():
    if request.method == 'POST':
        receiver = request.form.get('receiver')
        content = request.form.get('content')

        # Check if the receiver exists in the database
        receiver_user = User.query.filter_by(username=receiver).first()
        if not receiver_user:
            flash('Receiver does not exist. Please enter a valid username.')
            return redirect(url_for('main.send_message'))

        # Create a new block in the blockchain
        new_block = create_new_block(blockchain[-1], {
            'sender': current_user.username,
            'receiver': receiver,
            'content': content
        })
        blockchain.append(new_block)
        flash('Message sent successfully!')
        return redirect(url_for('main.dashboard'))
    return render_template('send_message.html')

@main.route('/view_messages')
@login_required
def view_messages():
    messages = [block.data for block in blockchain if isinstance(block.data, dict) and block.data.get('receiver') == current_user.username]
    return render_template('view_messages.html', messages=messages)

@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))