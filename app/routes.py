from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User
from app import db, static
from eth_account.messages import encode_defunct  # Use encode_defunct for message signing
from web3 import Web3
from app.blockchain import create_genesis_block, create_new_block  # Import blockchain functions
import re
import os
from app.models import Post, Comment
from app.models import Announcement
from app.models import User, Project, ProjectComment
from app.models import Group, GroupMember, GroupMessage
from werkzeug.utils import secure_filename
from app.models import Message 
from app.models import NFT


# Define the Blueprint
main = Blueprint('main', __name__)
UPLOAD_FOLDER = 'app/static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///your_database.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    # Import and register blueprints
    from app.routes import main
    app.register_blueprint(main)

    return app

# --------------------- Initialize blockchain ---------------------

blockchain = [create_genesis_block()]
#from flask import Flask
#app = Flask(__name__)

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
    

# --------------------- DASHBOARD ---------------------

@main.route('/dashboard')
@login_required
def dashboard():
    # Fetch groups where the current user is the admin
    admin_groups = Group.query.filter_by(admin_public_key=current_user.public_key).all()

    # Fetch groups where the current user is a member
    member_groups = Group.query.join(GroupMember).filter(GroupMember.member_public_key == current_user.public_key).all()

    # Combine the lists (if needed)
    groups = admin_groups + member_groups

    return render_template('dashboard.html', username=current_user.username, groups=groups)

# --------------------- SEND MESSAGE ---------------------

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

# --------------------- VIEW MESSAGE ---------------------

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

from flask import render_template, request, redirect, url_for, flash
from .models import Group, GroupMember, Post
from . import db

# --------------------- CREATE GROUP ---------------------

@main.route('/create_group', methods=['GET', 'POST'])
def create_group():
    if request.method == 'POST':
        group_name = request.form.get('group_name')
        admin_public_key = current_user.public_key  # Assuming the current user is the admin

        # Create the group
        new_group = Group(name=group_name, admin_public_key=admin_public_key)
        db.session.add(new_group)
        db.session.commit()

        flash('Group created successfully!', 'success')
        return redirect(url_for('main.dashboard'))

    return render_template('create_group.html')

# --------------------- Add a member to a group ---------------------

@main.route('/add_member/<int:group_id>', methods=['POST'])
@login_required
def add_member(group_id):
    group = Group.query.get_or_404(group_id)

    # Check if the current user is the admin
    if current_user.public_key != group.admin_public_key:
        flash('You do not have permission to add members to this group.', 'danger')
        return redirect(url_for('main.group_chat', group_id=group.id))

    # Get the member's public key from the form
    member_public_key = request.form.get('member_public_key')

    # Validate the public key
    if not re.match(r'^0x[a-fA-F0-9]{40}$', member_public_key):
        flash('Invalid public key. Please enter a valid Ethereum public key.', 'danger')
        return redirect(url_for('main.group_chat', group_id=group.id))

    # Check if the member already exists in the group
    existing_member = GroupMember.query.filter_by(group_id=group.id, member_public_key=member_public_key).first()
    if existing_member:
        flash('This member is already in the group.', 'warning')
        return redirect(url_for('main.group_chat', group_id=group.id))

    # Add the member
    new_member = GroupMember(group_id=group.id, member_public_key=member_public_key)
    db.session.add(new_member)
    db.session.commit()

    flash('Member added successfully!', 'success')
    return redirect(url_for('main.group_chat', group_id=group.id))



# --------------------- View a group and its members ---------------------

@main.route('/view_group/<int:group_id>')
def view_group(group_id):
    group = Group.query.get_or_404(group_id)
    members = GroupMember.query.filter_by(group_id=group.id).all()
    return render_template('view_group.html', group=group, members=members)

# Group Chat
@main.route('/group_chat/<int:group_id>')
@login_required
def group_chat(group_id):
    # Fetch the group
    group = Group.query.get_or_404(group_id)

    # Check if the current user is a member of the group
    is_member = GroupMember.query.filter_by(group_id=group.id, member_public_key=current_user.public_key).first()
    if not is_member and group.admin_public_key != current_user.public_key:
        flash('You are not a member of this group.', 'danger')
        return redirect(url_for('main.dashboard'))

    # Fetch group messages
    group_messages = GroupMessage.query.filter_by(group_id=group.id).order_by(GroupMessage.timestamp.asc()).all()

    return render_template('group_chat.html', group=group, group_messages=group_messages)

from app.models import GroupMessage
# --------------------- SEND GROUP MESSAGE ---------------------

@main.route('/send_group_message/<int:group_id>', methods=['POST'])
@login_required
def send_group_message(group_id):
    content = request.form.get('content')  # Ensure this matches the form field name

    if not content:
        return jsonify({"status": "error", "message": "Message content is required"}), 400

    # Save the message to the database
    new_message = GroupMessage(
        group_id=group_id,
        sender=current_user.public_key,
        content=content
    )
    db.session.add(new_message)
    db.session.commit()

    return jsonify({
        "status": "success",
        "content": content
    })
   
# --------------------- REMOVE MEMBER ---------------------

@main.route('/remove_member/<int:group_id>/<string:member_public_key>', methods=['POST'])
@login_required
def remove_member(group_id, member_public_key):
    group = Group.query.get_or_404(group_id)

    # Check if the current user is the admin
    if current_user.public_key != group.admin_public_key:
        flash('You do not have permission to remove members from this group.', 'danger')
        return redirect(url_for('main.group_chat', group_id=group.id))

    # Remove the member
    member = GroupMember.query.filter_by(group_id=group.id, member_public_key=member_public_key).first()
    if member:
        db.session.delete(member)
        db.session.commit()
        flash('Member removed successfully!', 'success')
    else:
        flash('Member not found.', 'danger')

    return redirect(url_for('main.group_chat', group_id=group.id))

# ---------------------  ---------------------
# Define the upload folder and allowed extensions
UPLOAD_FOLDER = 'app/static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Define the upload folder and allowed extensions
UPLOAD_FOLDER = 'app/static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --------------------- upload_group_image  ---------------------

@main.route('/upload_group_image/<int:group_id>', methods=['POST'])
@login_required
def upload_group_image(group_id):
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"status": "error", "message": "No selected file"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename).replace('\\', '/')  # Replace backslashes
        file.save(file_path)

        # Save the relative path to the database
        new_message = GroupMessage(
            group_id=group_id,
            sender=current_user.public_key,
            image=os.path.join('uploads', filename).replace('\\', '/')  # Replace backslashes
        )
        db.session.add(new_message)
        db.session.commit()

        return jsonify({
            "status": "success",
            "image_url": url_for('static', filename=os.path.join('uploads', filename).replace('\\', '/'))
        })

    return jsonify({"status": "error", "message": "Invalid file type"}), 400
# --------------------- LEAVE GROUP ---------------------

@main.route('/leave_group/<int:group_id>', methods=['POST'])
@login_required
def leave_group(group_id):
    group = Group.query.get_or_404(group_id)
    member = GroupMember.query.filter_by(group_id=group.id, member_public_key=current_user.public_key).first()

    if member:
        db.session.delete(member)
        db.session.commit()
        flash('You have left the group.', 'success')
    else:
        flash('You are not a member of this group.', 'danger')

    return redirect(url_for('main.dashboard'))

# --------------------- COMMUNITY  ---------------------

# Community Page
@main.route('/community', methods=['GET', 'POST'])
@login_required
def community():
    if request.method == 'POST':
        content = request.form.get('content')
        template = request.form.get('template')  # Get the selected template
        if content:
            new_post = Post(author=current_user.public_key, content=content, template=template)
            db.session.add(new_post)
            db.session.commit()
            flash('Post created successfully!', 'success')
        else:
            flash('Post content cannot be empty.', 'danger')

    # Fetch posts and ensure upvotes are not None
    posts = Post.query.order_by(Post.timestamp.desc()).all()
    for post in posts:
        if post.upvotes is None:
            post.upvotes = 0

    return render_template('community.html', posts=posts)
# Upvote a Post
@main.route('/upvote/<int:post_id>', methods=['POST'])
@login_required
def upvote(post_id):
    post = Post.query.get_or_404(post_id)
    post.upvotes += 1
    db.session.commit()
    return jsonify({'status': 'success', 'upvotes': post.upvotes})

# Downvote a Post
@main.route('/downvote/<int:post_id>', methods=['POST'])
@login_required
def downvote(post_id):
    post = Post.query.get_or_404(post_id)
    post.downvotes += 1
    db.session.commit()
    return jsonify({'status': 'success', 'downvotes': post.downvotes})

# Add a Comment
@main.route('/comment/<int:post_id>', methods=['POST'])
@login_required
def comment(post_id):
    content = request.form.get('content')
    if content:
        new_comment = Comment(post_id=post_id, author=current_user.public_key, content=content)
        db.session.add(new_comment)
        db.session.commit()
        flash('Comment added successfully!', 'success')
    else:
        flash('Comment cannot be empty.', 'danger')
    return redirect(url_for('main.community'))

@main.route('/create_post', methods=['GET', 'POST'])
@login_required
def create_post():
    if request.method == 'POST':
        content = request.form.get('content')
        template = request.form.get('template')
        if content:
            new_post = Post(
                author=current_user.public_key,
                content=content,
                template=template
            )
            db.session.add(new_post)
            db.session.commit()
            flash('Post created successfully!', 'success')
            return redirect(url_for('main.community'))
        else:
            flash('Post content cannot be empty.', 'danger')
    return render_template('create_post.html')

@main.route('/community/web3')
@login_required
def web3_community():
    group = Group.query.first()
    posts = Post.query.filter_by(category='web3').order_by(Post.timestamp.desc()).all()
    announcements = Announcement.query.filter_by(category='web3').order_by(Announcement.timestamp.desc()).limit(5).all()
    return render_template('web3_community.html', posts=posts, announcements=announcements, group=group)

@main.route('/community/trading')
@login_required
def trading_community():
    posts = Post.query.filter_by(category='trading').order_by(Post.timestamp.desc()).all()
    announcements = Announcement.query.filter_by(category='trading').order_by(Announcement.timestamp.desc()).limit(5).all()
    return render_template('trading_community.html', posts=posts, announcements=announcements)

# Add similar routes for other sub-communities (e.g., competition, blockchain, etc.)
@main.route('/community/competition')
@login_required
def competition_community():
    posts = Post.query.filter_by(category='competition').order_by(Post.timestamp.desc()).all()
    announcements = Announcement.query.filter_by(category='competition').order_by(Announcement.timestamp.desc()).limit(5).all()
    return render_template('competition_community.html', posts=posts, announcements=announcements)

@main.route('/community/blockchain')
@login_required
def blockchain_community():
    posts = Post.query.filter_by(category='blockchain').order_by(Post.timestamp.desc()).all()
    announcements = Announcement.query.filter_by(category='blockchain').order_by(Announcement.timestamp.desc()).limit(5).all()
    return render_template('blockchain_community.html', posts=posts, announcements=announcements)

@main.route('/group_chat')
@login_required
def group_chat_home():
    # Fetch all groups or display a default group chat
    groups = Group.query.all()
    return render_template('group_chat_home.html', groups=groups)

# Projects Page
@main.route('/projects', methods=['GET', 'POST'])
def projects():
    if request.method == 'POST':
        # Handle project submission
        title = request.form.get('title')
        description = request.form.get('description')
        image = request.files.get('image')
        video = request.form.get('video')
        links = request.form.get('links')
        category = request.form.get('category')
        tags = request.form.get('tags')

        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            image.save(filepath)
            image_url = os.path.join('uploads', filename)
        else:
            image_url = None

        new_project = Project(
            title=title,
            description=description,
            image=image_url,
            video=video,
            links=links,
            category=category,
            tags=tags,
            author=current_user.public_key
        )
        db.session.add(new_project)
        db.session.commit()
        flash('Project submitted successfully!', 'success')
        return redirect(url_for('main.projects'))

    # Fetch all projects
    projects = Project.query.order_by(Project.timestamp.desc()).all()
    return render_template('projects.html', projects=projects)

# Project Detail Page
@main.route('/project/<int:project_id>')
def project_detail(project_id):
    project = Project.query.get_or_404(project_id)
    return render_template('project_detail.html', project=project)

# Like a Project
@main.route('/like_project/<int:project_id>', methods=['POST'])
@login_required
def like_project(project_id):
    project = Project.query.get_or_404(project_id)
    project.likes += 1
    db.session.commit()
    return jsonify({'status': 'success', 'likes': project.likes})

# Dislike a Project
@main.route('/dislike_project/<int:project_id>', methods=['POST'])
@login_required
def dislike_project(project_id):
    project = Project.query.get_or_404(project_id)
    project.dislikes += 1
    db.session.commit()
    return jsonify({'status': 'success', 'dislikes': project.dislikes})

# Add a Comment to a Project
@main.route('/comment_project/<int:project_id>', methods=['POST'])
@login_required
def comment_project(project_id):
    content = request.form.get('content')
    if content:
        new_comment = ProjectComment(
            project_id=project_id,
            author=current_user.public_key,
            content=content
        )
        db.session.add(new_comment)
        db.session.commit()
        flash('Comment added successfully!', 'success')
    else:
        flash('Comment cannot be empty.', 'danger')
    return redirect(url_for('main.project_detail', project_id=project_id))

@main.route('/delete_project/<int:project_id>', methods=['POST'])
@login_required
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)

    # Check if the current user is the author of the project
    if current_user.public_key != project.author:
        return jsonify({"status": "error", "message": "You are not authorized to delete this project."}), 403

    # Delete the project
    db.session.delete(project)
    db.session.commit()

    return jsonify({"status": "success", "message": "Project deleted successfully."})

@main.route('/search_posts', methods=['GET'])
def search_posts():
    query = request.args.get('query', '').strip()  # Get the search query from the URL
    if query:
        # Search for posts containing the query in their content
        results = Post.query.filter(Post.content.contains(query)).all()
    else:
        results = []
    return render_template('search_results.html', search_results=results, query=query)

@main.route('/community/nft_marketplace')  # Updated route
@login_required
def nft_marketplace_community():
    # Fetch posts and announcements
    posts = Post.query.filter_by(category='nft_marketplace').order_by(Post.timestamp.desc()).all()
    announcements = Announcement.query.filter_by(category='nft_marketplace').order_by(Announcement.timestamp.desc()).limit(5).all()

    # Fetch listed NFTs
    nfts = NFT.query.filter_by(listed=True).all()

    # Pass all data to the template
    return render_template('nft_marketplace_community.html', posts=posts, announcements=announcements, nfts=nfts)
@main.route('/list_nft', methods=['GET', 'POST'])
@login_required
def list_nft():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        image = request.files['image']  # Get the uploaded image file
        price = float(request.form.get('price'))
        seller = current_user.public_key  # Set the seller to the current user's public key
        owner = current_user.public_key  # Assuming the seller is also the owner initially
        chain = request.form.get('chain')

        # Save the image to the uploads folder
        if image:
            filename = secure_filename(image.filename)
            image_path = f"uploads/{filename}"
            image.save(os.path.join(current_app.static_folder, image_path))
        else:
            image_path = "uploads/default-nft.png"  # Default image if none is uploaded

        # Create a new NFT object
        new_nft = NFT(
            name=name,
            description=description,
            image=image_path,
            price=price,
            seller=seller,  # Set the seller field
            owner=owner,
            chain=chain
        )

        # Add to the database
        db.session.add(new_nft)
        db.session.commit()

        flash('NFT listed successfully!', 'success')
        return redirect(url_for('main.nft_marketplace_community'))

    return render_template('list_nft.html')


@main.route('/nft/buy/<int:nft_id>', methods=['POST'])
@login_required
def buy_nft(nft_id):
    nft = NFT.query.get_or_404(nft_id)

    if not nft.listed:
        flash('This NFT is not listed for sale.', 'danger')
        return redirect(url_for('main.nft_marketplace_community'))

    # Transfer ownership (simulated for now)
    nft.owner = current_user.public_key
    nft.listed = False
    db.session.commit()

    flash('NFT purchased successfully!', 'success')
    return redirect(url_for('main.nft_marketplace_community'))
@main.route('/nft/<int:nft_id>')
@login_required
def view_nft(nft_id):
    nft = NFT.query.get_or_404(nft_id)
    return render_template('view_nft.html', nft=nft)