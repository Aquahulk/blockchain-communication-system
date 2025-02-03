from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User
from app import db
from eth_account.messages import encode_defunct  # Use encode_defunct for message signing
from web3 import Web3
from app.blockchain import create_genesis_block, create_new_block  # Import blockchain functions

# Define the Blueprint
main = Blueprint('main', __name__)

# Initialize blockchain
blockchain = [create_genesis_block()]

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/web3_login', methods=['POST'])
def web3_login():
    data = request.json
    public_key = data.get('public_key')
    signature = data.get('signature')
    message = data.get('message')

    if not public_key or not signature or not message:
        return jsonify({"status": "error", "message": "Missing parameters"}), 400

    try:
        # Encode the message properly
        message_hash = encode_defunct(text=message)

        # Recover the Ethereum address from the signature
        recovered_address = Web3().eth.account.recover_message(message_hash, signature=signature)

        # Validate the recovered address
        if recovered_address.lower() == public_key.lower():
            # Check if the user exists, otherwise create a new one
            user = User.query.filter_by(public_key=public_key).first()
            if not user:
                user = User(public_key=public_key, username=public_key, password="")  # No password for Web3 login
                db.session.add(user)
                db.session.commit()

            # Log the user in
            login_user(user)
            return jsonify({"status": "success"})
        else:
            return jsonify({"status": "error", "message": "Invalid signature"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

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
        receiver_user = User.query.filter_by(public_key=receiver).first()
        if not receiver_user:
            flash('Receiver does not exist. Please enter a valid public key.')
            return redirect(url_for('main.send_message'))

        # Create a new block in the blockchain
        new_block = create_new_block(blockchain[-1], {
            'sender': current_user.public_key,
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
    messages = [block.data for block in blockchain if isinstance(block.data, dict) and block.data.get('receiver') == current_user.public_key]
    return render_template('view_messages.html', messages=messages)

@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))
