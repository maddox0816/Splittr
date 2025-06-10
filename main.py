import os
from flask import Flask, request, redirect, url_for, flash, get_flashed_messages, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_, and_, not_
from jinja2 import Environment, DictLoader

# --- App Initialization ---
app = Flask(__name__)

# --- Configuration ---
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a_very_secret_key_for_prod')
# Database file name changed to reflect new schema
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///splittr_app_v2.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- Database and Login Manager Setup ---
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# --- Database Models ---

class Friendship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user1_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user2_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=True) # This is the Venmo username
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class FriendRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    payer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    payer = db.relationship('User', backref='paid_expenses')
    debts = db.relationship('Debt', backref='expense', cascade="all, delete-orphan")

class Debt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    expense_id = db.Column(db.Integer, db.ForeignKey('expense.id'), nullable=False)
    debtor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    paid_amount = db.Column(db.Float, default=0.0)
    is_fully_paid = db.Column(db.Boolean, default=False)
    debtor = db.relationship('User', foreign_keys=[debtor_id])

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- HTML Templates ---
HOME_PAGE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Splittr - Effortless Expense Sharing</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700;900&display=swap" rel="stylesheet">
    <!-- AOS Animation Library CSS -->
    <link href="https://unpkg.com/aos@2.3.1/dist/aos.css" rel="stylesheet">
    <style>
        body { 
            font-family: 'Inter', sans-serif; 
            background-color: #020617; /* slate-950 */
        }
        .gradient-text {
            background-image: linear-gradient(to right, #818cf8, #38bdf8);
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
        }
    </style>
</head>
<body class="text-slate-200">

    <!-- Header -->
    <header class="absolute top-0 left-0 w-full z-10 py-6 px-4">
        <div class="container mx-auto max-w-6xl flex justify-between items-center">
            <h1 class="text-2xl font-bold gradient-text">Splittr</h1>
            <a href="/login" class="bg-indigo-600 hover:bg-indigo-500 text-white font-bold py-2 px-5 rounded-lg shadow-md transition-transform transform hover:scale-105">
                Login
            </a>
        </div>
    </header>

    <!-- Hero Section -->
    <main class="relative isolate overflow-hidden">
        <div class="absolute inset-0 bg-slate-900/50 backdrop-blur-sm z-0"></div>
        <div class="absolute -top-48 left-1/2 -z-10 -translate-x-1/2 transform-gpu blur-3xl" aria-hidden="true">
            <div class="aspect-[1108/632] w-[69.25rem] bg-gradient-to-r from-[#80caff] to-[#4f46e5] opacity-20" style="clip-path: polygon(73.6% 51.7%, 91.7% 11.8%, 100% 46.4%, 97.4% 82.2%, 92.5% 84.9%, 75.7% 64.3%, 55.3% 47.5%, 46.5% 49.4%, 45% 62.9%, 50.3% 87.2%, 21.3% 64.1%, 0.1% 100%, 1.4% 98.3%, 17.4% 92.5%, 27.5% 78.7%, 76.5% 97.2%, 73.6% 51.7%)"></div>
        </div>
        <div class="mx-auto max-w-6xl px-6 lg:px-8 py-32 sm:py-48 lg:py-56 text-center relative z-10">
            <h1 class="text-4xl font-black tracking-tight text-white sm:text-6xl" data-aos="fade-down">
                Stop chasing payments.
                <br>
                Start <span class="gradient-text">Splitting</span>.
            </h1>
            <p class="mt-6 text-lg leading-8 text-slate-300 max-w-2xl mx-auto" data-aos="fade-up" data-aos-delay="200">
                From dinners out to group trips, Splittr is the simplest way to track shared expenses with friends. No more awkward conversations, just clear balances and easy settlements.
            </p>
            <div class="mt-10 flex items-center justify-center gap-x-6" data-aos="fade-up" data-aos-delay="400">
                <a href="/login" class="rounded-md bg-indigo-600 px-6 py-3 text-lg font-semibold text-white shadow-lg hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 transition-transform transform hover:scale-105">Get Started</a>
            </div>
        </div>
    </main>

    <!-- Features Section -->
    <section class="bg-slate-900 py-24 sm:py-32">
        <div class="mx-auto max-w-6xl px-6 lg:px-8">
            <div class="mx-auto max-w-2xl lg:text-center" data-aos="fade-up">
                <h2 class="text-base font-semibold leading-7 text-indigo-400">Everything You Need</h2>
                <p class="mt-2 text-3xl font-bold tracking-tight text-white sm:text-4xl">The Ultimate IOU Tracker</p>
                <p class="mt-6 text-lg leading-8 text-slate-300">
                    We built Splittr with one goal: to make sharing costs as painless as possible. Here's how we do it.
                </p>
            </div>
            <div class="mx-auto mt-16 max-w-2xl sm:mt-20 lg:mt-24 lg:max-w-none">
                <dl class="grid max-w-xl grid-cols-1 gap-x-8 gap-y-16 lg:max-w-none lg:grid-cols-3">
                    <!-- Feature 1 -->
                    <div class="flex flex-col items-center text-center lg:items-start lg:text-left" data-aos="fade-up" data-aos-delay="100">
                        <dt class="flex items-center gap-x-3 text-base font-semibold leading-7 text-white">
                            <svg class="h-6 w-6 text-indigo-400" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
                            Connect with Friends
                        </dt>
                        <dd class="mt-4 flex flex-auto flex-col text-base leading-7 text-slate-300">
                            <p class="flex-auto">Find and add your friends using their Venmo username. Send requests, build your circle, and keep everyone in one place.</p>
                        </dd>
                    </div>

                    <!-- Feature 2 -->
                    <div class="flex flex-col items-center text-center lg:items-start lg:text-left" data-aos="fade-up" data-aos-delay="200">
                        <dt class="flex items-center gap-x-3 text-base font-semibold leading-7 text-white">
                            <svg class="h-6 w-6 text-indigo-400" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10 10-4.5 10-10S17.5 2 12 2Z"/><path d="M16.2 7.8 11.4 12l4.8 4.2"/><path d="M8 12h3"/></svg>
                            Flexible Expense Splitting
                        </dt>
                        <dd class="mt-4 flex flex-auto flex-col text-base leading-7 text-slate-300">
                            <p class="flex-auto">Log an expense and split it with multiple friends at once. Choose to split the cost evenly or enter custom amounts for complete control.</p>
                        </dd>
                    </div>

                    <!-- Feature 3 -->
                    <div class="flex flex-col items-center text-center lg:items-start lg:text-left" data-aos="fade-up" data-aos-delay="300">
                        <dt class="flex items-center gap-x-3 text-base font-semibold leading-7 text-white">
                            <svg class="h-6 w-6 text-indigo-400" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m16 16-4-4 4-4"/><path d="m8 16-4-4 4-4"/><path d="M12 2v20"/></svg>
                            Clear, Real-Time Balances
                        </dt>
                        <dd class="mt-4 flex flex-auto flex-col text-base leading-7 text-slate-300">
                            <p class="flex-auto">Your dashboard gives you a live, at-a-glance view of who owes who. Green means they owe you, red means you owe them. Simple.</p>
                        </dd>
                    </div>

                     <!-- Feature 4 -->
                     <div class="flex flex-col items-center text-center lg:items-start lg:text-left" data-aos="fade-up" data-aos-delay="100">
                        <dt class="flex items-center gap-x-3 text-base font-semibold leading-7 text-white">
                            <svg class="h-6 w-6 text-indigo-400" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m3 11 18-5L17 21l-5-5Z"/><path d="m11 11 5 5"/></svg>
                            Partial & Full Settlements
                        </dt>
                        <dd class="mt-4 flex flex-auto flex-col text-base leading-7 text-slate-300">
                            <p class="flex-auto">Record payments with ease. Log the exact amount a friend paid you, whether it's the full balance or just a partial payment, and watch the numbers update instantly.</p>
                        </dd>
                    </div>

                    <!-- Feature 5 -->
                    <div class="flex flex-col items-center text-center lg:items-start lg:text-left" data-aos="fade-up" data-aos-delay="200">
                        <dt class="flex items-center gap-x-3 text-base font-semibold leading-7 text-white">
                            <svg class="h-6 w-6 text-indigo-400" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="4" rx="2" ry="2"/><line x1="16" x2="16" y1="2" y2="6"/><line x1="8" x2="8" y1="2" y2="6"/><line x1="3" x2="21" y1="10" y2="10"/><path d="M8 14h.01"/><path d="M12 14h.01"/><path d="M16 14h.01"/><path d="M8 18h.01"/><path d="M12 18h.01"/><path d="M16 18h.01"/></svg>
                            Detailed History
                        </dt>
                        <dd class="mt-4 flex flex-auto flex-col text-base leading-7 text-slate-300">
                            <p class="flex-auto">Never forget who paid for what. Every expense and settlement is recorded, giving you a complete history of your shared costs.</p>
                        </dd>
                    </div>

                    <!-- Feature 6 -->
                    <div class="flex flex-col items-center text-center lg:items-start lg:text-left" data-aos="fade-up" data-aos-delay="300">
                        <dt class="flex items-center gap-x-3 text-base font-semibold leading-7 text-white">
                            <svg class="h-6 w-6 text-indigo-400" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.73 18a2.73 2.73 0 0 1-3.85 3.85l-1.42-1.42a2.73 2.73 0 0 1 3.85-3.85Z"/><path d="M1.42 2.58a2.73 2.73 0 0 0 3.85 3.85l1.42 1.42a2.73 2.73 0 0 0-3.85-3.85Z"/><path d="m12 12-2-2 4-4 2 2-4 4Z"/><path d="M9.03 11.97 12 15l-3 3-1.42-1.42a2.73 2.73 0 0 1 0-3.85L9.03 11.97Z"/><path d="M14.97 8.97 12 6l3-3 1.42 1.42a2.73 2.73 0 0 1 0 3.85L14.97 8.97Z"/></svg>
                            Secure & Private
                        </dt>
                        <dd class="mt-4 flex flex-auto flex-col text-base leading-7 text-slate-300">
                            <p class="flex-auto">Your account and financial data are yours alone. Sign up for a secure account and manage your expenses with peace of mind.</p>
                        </dd>
                    </div>
                </dl>
            </div>
        </div>
    </section>

    <!-- Footer -->
    <footer class="bg-slate-950">
        <div class="mx-auto max-w-7xl overflow-hidden px-6 py-12 lg:px-8">
            <p class="text-center text-xs leading-5 text-slate-400">
                &copy; 2025 Splittr. All rights reserved.
            </p>
        </div>
    </footer>

    <!-- AOS Animation Library JS -->
    <script src="https://unpkg.com/aos@2.3.1/dist/aos.js"></script>
    <script>
      AOS.init({
        duration: 800, // Animation duration
        once: true,    // Whether animation should happen only once
      });
    </script>

</body>
</html>

"""

LAYOUT_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Splittr</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&display=swap" rel="stylesheet">
    <style> body { font-family: 'Inter', sans-serif; } </style>
</head>
<body class="bg-slate-900 text-white">
    <div class="container mx-auto px-4 py-8 max-w-4xl">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="p-4 mb-4 text-sm rounded-lg {% if category == 'error' %} bg-red-800 text-red-300 {% elif category == 'success' %} bg-green-800 text-green-300 {% else %} bg-blue-800 text-blue-300 {% endif %}" role="alert">
                        {{ message }}
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        {% block content %}{% endblock %}
    </div>
</body>
</html>
"""

LOGIN_TEMPLATE = """
{% extends "layout.html" %}
{% block content %}
<div class="max-w-md mx-auto mt-10 bg-slate-800 p-8 rounded-lg shadow-lg">
    <h1 class="text-3xl font-bold text-center text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-cyan-400 mb-6">
        {% if form_type == 'login' %}Welcome to Splittr{% else %}Join Splittr{% endif %}
    </h1>
    <form method="POST" class="space-y-4">
        {% if form_type == 'register' %}
        <div>
            <label for="name" class="block mb-2 text-sm font-medium text-slate-300">Full Name</label>
            <input type="text" name="name" class="w-full bg-slate-700 text-white p-3 rounded-lg border border-slate-600" required>
        </div>
        <div>
            <label for="username" class="block mb-2 text-sm font-medium text-slate-300">Venmo Username</label>
            <p class="text-xs text-slate-400 mb-1">Enter a fun username if you don't have venmo</p>
            <input type="text" name="username" class="w-full bg-slate-700 text-white p-3 rounded-lg border border-slate-600" required>
        </div>
        {% endif %}
        <div>
            <label for="email" class="block mb-2 text-sm font-medium text-slate-300">Email</label>
            <input type="email" name="email" class="w-full bg-slate-700 text-white p-3 rounded-lg border border-slate-600" required>
        </div>
        <div>
            <label for="password" class="block mb-2 text-sm font-medium text-slate-300">Password</label>
            <input type="password" name="password" class="w-full bg-slate-700 text-white p-3 rounded-lg border border-slate-600" required>
        </div>
        <button type="submit" class="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-bold py-3 px-4 rounded-lg shadow-md transition-all">
            {% if form_type == 'login' %}Login{% else %}Sign Up{% endif %}
        </button>
    </form>
    <div class="text-center mt-4">
        <a href="{{ url_for('register') if form_type == 'login' else url_for('login') }}" class="text-cyan-400 hover:text-cyan-300">
            {% if form_type == 'login' %}Need an account? Sign Up{% else %}Already have an account? Login{% endif %}
        </a>
    </div>
</div>
{% endblock %}
"""

DASHBOARD_TEMPLATE = """
{% extends "layout.html" %}
{% block content %}
<header class="flex justify-between items-center mb-6">
    <div>
        <h1 class="text-3xl sm:text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-cyan-400">
            Splittr
        </h1>
        <p class="text-slate-400">Welcome, {{ current_user.name }}!</p>
    </div>
    <a href="{{ url_for('logout') }}" class="bg-red-800/50 hover:bg-red-700/50 text-red-300 p-2 rounded-lg">Logout</a>
</header>
<nav class="flex justify-center items-center gap-4 my-6">
    <a href="{{ url_for('dashboard') }}" class="px-4 py-2 rounded-lg font-semibold bg-indigo-600 text-white">Dashboard</a>
    <a href="{{ url_for('friends') }}" class="relative px-4 py-2 rounded-lg font-semibold bg-slate-700 text-slate-300 hover:bg-slate-600">
        Friends
        {% if request_count > 0 %}
        <span class="absolute -top-2 -right-2 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">{{ request_count }}</span>
        {% endif %}
    </a>
    <a href="{{ url_for('add_expense') }}" class="px-4 py-2 rounded-lg font-semibold bg-cyan-600 hover:bg-cyan-500 text-white">Add Expense</a>
</nav>
<main>
    <h2 class="text-2xl font-bold mb-4">Your Balances</h2>
    {% if balances %}
        <div class="space-y-3">
        {% for friend, balance in balances.items() %}
            <div class="bg-slate-800 p-4 rounded-lg shadow-md flex flex-col sm:flex-row justify-between items-center gap-4">
                <div>
                    <h3 class="text-xl font-bold">{{ friend.name }}</h3>
                    {% if friend.username %}
                    <p class="text-sm text-cyan-400">@{{ friend.username }}</p>
                    {% endif %}
                    <p class="mt-1 font-semibold {% if balance > 0.005 %}text-green-400{% elif balance < -0.005 %}text-red-400{% else %}text-slate-400{% endif %}">
                        {% if balance > 0.005 %}
                            Owes you ${{ "%.2f"|format(balance) }}
                        {% elif balance < -0.005 %}
                            You owe ${{ "%.2f"|format(balance|abs) }}
                        {% else %}
                            All settled up
                        {% endif %}
                    </p>
                </div>
                <div>
                {% if balance > 0.005 %}
                    <a href="{{ url_for('settle', friend_id=friend.id) }}" class="bg-green-600 hover:bg-green-500 text-white font-bold py-2 px-4 rounded-lg">Settle Up</a>
                {% endif %}
                </div>
            </div>
        {% endfor %}
        </div>
    {% else %}
        <div class="text-center py-10 px-4 bg-slate-800/50 rounded-lg">
            <p class="text-slate-400">No balances to show. Add an expense or make some friends!</p>
        </div>
    {% endif %}
</main>
{% endblock %}
"""

FRIENDS_TEMPLATE = """
{% extends "layout.html" %}
{% block content %}
<header class="flex justify-between items-center mb-6">
    <h1 class="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-cyan-400">Manage Friends</h1>
    <a href="{{ url_for('dashboard') }}" class="text-cyan-400 hover:text-cyan-300">&larr; Back to Dashboard</a>
</header>
<div class="grid md:grid-cols-2 gap-6">
    <div>
        <div class="bg-slate-800 p-6 rounded-lg mb-6">
            <h3 class="text-xl font-bold mb-3">Find Friends</h3>
            <input type="text" id="user-search" placeholder="Search by Venmo username..." class="w-full bg-slate-700 text-white p-2 rounded-lg border border-slate-600">
            <div id="search-results" class="mt-3 space-y-2"></div>
        </div>
        <div class="bg-slate-800 p-6 rounded-lg">
            <h3 class="text-xl font-bold mb-3">Your Friends ({{ friends|length }})</h3>
            <div class="space-y-2">
                {% for friend in friends %}
                    <div class="bg-slate-700/50 p-3 rounded-md">
                        <p class="font-semibold">{{ friend.name }}</p>
                        {% if friend.username %}<p class="text-sm text-cyan-400">@{{ friend.username }}</p>{% endif %}
                    </div>
                {% else %}
                    <p class="text-slate-400">You haven't added any friends yet.</p>
                {% endfor %}
            </div>
        </div>
    </div>
    <div class="bg-slate-800 p-6 rounded-lg">
        <h3 class="text-xl font-bold mb-3">Friend Requests ({{ requests|length }})</h3>
        <div class="space-y-2">
            {% for req in requests %}
            <div class="flex justify-between items-center bg-slate-700/50 p-3 rounded-md">
                <span>{{ req.sender.name }} sent you a request.</span>
                <div class="flex gap-2">
                    <a href="{{ url_for('handle_request', request_id=req.id, action='accept') }}" class="bg-green-600 hover:bg-green-500 p-2 rounded-lg">Accept</a>
                    <a href="{{ url_for('handle_request', request_id=req.id, action='decline') }}" class="bg-red-600 hover:bg-red-500 p-2 rounded-lg">Decline</a>
                </div>
            </div>
            {% else %}
                <p class="text-slate-400">No new requests.</p>
            {% endfor %}
        </div>
    </div>
</div>
<script>
    let searchTimeout;
    const searchInput = document.getElementById('user-search');
    const resultsContainer = document.getElementById('search-results');
    searchInput.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        const query = e.target.value;
        if (query.length < 2) {
            resultsContainer.innerHTML = '';
            return;
        }
        searchTimeout = setTimeout(() => {
            fetch(`/api/search_users?q=${query}`)
                .then(response => response.json())
                .then(data => {
                    resultsContainer.innerHTML = '';
                    if (data.length > 0) {
                        data.forEach(user => {
                            const userDiv = document.createElement('div');
                            userDiv.className = 'flex justify-between items-center bg-slate-700/50 p-3 rounded-md';
                            userDiv.innerHTML = `
                                <div>
                                    <p class="font-semibold">${user.name}</p>
                                    <p class="text-sm text-cyan-400">@${user.username}</p>
                                </div>
                                <a href="/send_request/${user.id}" class="bg-cyan-600 hover:bg-cyan-500 p-2 text-sm rounded-lg">Send Request</a>
                            `;
                            resultsContainer.appendChild(userDiv);
                        });
                    } else {
                        resultsContainer.innerHTML = '<p class="text-slate-400">No users found.</p>';
                    }
                });
        }, 300);
    });
</script>
{% endblock %}
"""

ADD_EXPENSE_TEMPLATE = """
{% extends "layout.html" %}
{% block content %}
<div class="max-w-lg mx-auto bg-slate-800 p-8 rounded-lg shadow-lg">
    <div class="flex justify-between items-center mb-6">
      <h2 class="text-2xl font-bold">Log a New Expense</h2>
      <a href="{{ url_for('dashboard') }}" class="text-cyan-400 hover:text-cyan-300">&larr; Back to Dashboard</a>
    </div>
    <form method="POST" class="space-y-6">
        <div>
            <label for="description" class="block mb-2 text-sm font-medium text-slate-300">Description</label>
            <input type="text" name="description" class="w-full bg-slate-700 text-white p-3 rounded-lg border border-slate-600" required>
        </div>
        <div>
            <label for="amount" class="block mb-2 text-sm font-medium text-slate-300">Total Amount You Paid</label>
            <input type="number" name="total_amount" id="total_amount" min="0.01" step="0.01" class="w-full bg-slate-700 text-white p-3 rounded-lg border border-slate-600" required>
        </div>
        <div>
            <label class="block mb-2 text-sm font-medium text-slate-300">Split With</label>
            <div class="max-h-40 overflow-y-auto space-y-2 p-3 bg-slate-900/50 rounded-lg border border-slate-700">
                {% for friend in friends %}
                <label class="flex items-center gap-3 p-2 rounded-md hover:bg-slate-700/50 cursor-pointer">
                    <input type="checkbox" name="friend_ids" value="{{ friend.id }}" class="friend-checkbox w-5 h-5 bg-slate-600 border-slate-500 rounded text-cyan-500 focus:ring-cyan-600">
                    <span>{{ friend.name }}</span>
                </label>
                {% else %}
                <p class="text-slate-400 text-center">You need to add friends first.</p>
                {% endfor %}
            </div>
        </div>
        <div>
            <label class="block mb-2 text-sm font-medium text-slate-300">Split Method</label>
            <div class="flex items-center gap-6 p-3 bg-slate-900/50 rounded-lg border border-slate-700">
                <label class="flex items-center gap-2 cursor-pointer"><input type="radio" name="split_method" value="even" checked onchange="toggleCustomAmounts(false)"> Split Evenly</label>
                <label class="flex items-center gap-2 cursor-pointer"><input type="radio" name="split_method" value="custom" onchange="toggleCustomAmounts(true)"> Custom Amounts</label>
            </div>
        </div>
        <div id="custom-amounts-section" class="hidden space-y-3 pt-4 border-t border-slate-700">
             <p class="text-sm text-slate-400">Enter what each person owes. The remainder is your share. Must add up to the total.</p>
        </div>
        <button type="submit" class="w-full bg-cyan-600 hover:bg-cyan-500 text-white font-bold py-3 px-4 rounded-lg">Add Expense</button>
    </form>
</div>
<script>
    const customAmountsSection = document.getElementById('custom-amounts-section');
    const friendCheckboxes = document.querySelectorAll('.friend-checkbox');
    function toggleCustomAmounts(show) {
        if (show) {
            customAmountsSection.classList.remove('hidden');
            updateCustomAmountInputs();
        } else {
            customAmountsSection.classList.add('hidden');
            customAmountsSection.innerHTML = '<p class="text-sm text-slate-400">Enter what each person owes. The remainder is your share. Must add up to the total.</p>';
        }
    }
    function updateCustomAmountInputs() {
        const baseHtml = '<p class="text-sm text-slate-400">Enter what each person owes. The remainder is your share. Must add up to the total.</p>';
        customAmountsSection.innerHTML = baseHtml;
        friendCheckboxes.forEach(checkbox => {
            if (checkbox.checked) {
                const friendName = checkbox.nextElementSibling.textContent;
                const friendId = checkbox.value;
                const inputGroup = document.createElement('div');
                inputGroup.className = 'flex items-center gap-2';
                inputGroup.innerHTML = `
                    <label for="custom_amount_${friendId}" class="w-1/3 text-slate-300">${friendName}:</label>
                    <div class="relative w-2/3">
                        <span class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">$</span>
                        <input type="number" name="custom_amount_${friendId}" min="0" step="0.01" placeholder="0.00" class="w-full bg-slate-700 text-white p-2 pl-7 rounded-lg border border-slate-600">
                    </div>
                `;
                customAmountsSection.appendChild(inputGroup);
            }
        });
    }
    friendCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', () => {
            if (document.querySelector('input[name="split_method"][value="custom"]').checked) {
                updateCustomAmountInputs();
            }
        });
    });
</script>
{% endblock %}
"""

SETTLE_TEMPLATE = """
{% extends "layout.html" %}
{% block content %}
<div class="max-w-md mx-auto bg-slate-800 p-8 rounded-lg shadow-lg">
    <div class="flex justify-between items-center mb-6">
      <h2 class="text-2xl font-bold">Settle with {{ friend.name }}</h2>
      <a href="{{ url_for('dashboard') }}" class="text-cyan-400 hover:text-cyan-300">&larr; Back to Dashboard</a>
    </div>
    <div class="mb-4 p-3 bg-green-900/50 border border-green-500/30 rounded-lg">
        <p class="text-slate-300">Current amount they owe you:</p>
        <p class="text-2xl font-bold text-green-400">${{ "%.2f"|format(balance) }}</p>
    </div>
    <form method="POST" class="space-y-4">
        <div>
            <label for="amount" class="block mb-2 text-sm font-medium text-slate-300">Payment Amount Received</label>
            <input type="number" name="amount" value="{{ "%.2f"|format(balance) }}" min="0.01" max="{{ "%.2f"|format(balance) }}" step="0.01" class="w-full bg-slate-700 text-white p-3 rounded-lg border border-slate-600" required>
        </div>
        <button type="submit" class="w-full bg-green-600 hover:bg-green-500 text-white font-bold py-3 px-4 rounded-lg">Record Payment</button>
    </form>
</div>
{% endblock %}
"""

PAST_EXPENSES_TEMPLATE = """
{% extends "layout.html" %}
{% block content %}
<div class="max-w-2xl mx-auto">
    <div class="flex justify-between items-center mb-6">
        <h2 class="text-2xl font-bold">Past Expenses</h2>
        <a href="{{ url_for('dashboard') }}" class="text-cyan-400 hover:text-cyan-300">&larr; Back to Dashboard</a>
    </div>
    <div class="mb-8">
        <h3 class="text-xl font-semibold mb-2">Expenses You Paid</h3>
        {% if paid_expenses %}
            <ul class="space-y-3">
                {% for exp in paid_expenses %}
                <li class="bg-slate-800 p-4 rounded-lg shadow flex flex-col">
                    <span class="font-bold">{{ exp.description }}</span>
                    <span class="text-slate-400 text-sm">Total: ${{ "%.2f"|format(exp.total_amount) }}</span>
                    <span class="text-slate-400 text-sm">Split with: 
                        {% for d in exp.debts %}
                            {{ d.debtor.name }}{% if not loop.last %}, {% endif %}
                        {% endfor %}
                    </span>
                </li>
                {% endfor %}
            </ul>
        {% else %}
            <p class="text-slate-400">No expenses paid by you yet.</p>
        {% endif %}
    </div>
    <div>
        <h3 class="text-xl font-semibold mb-2">Expenses You Owe</h3>
        {% if owed_expenses %}
            <ul class="space-y-3">
                {% for d in owed_expenses %}
                <li class="bg-slate-800 p-4 rounded-lg shadow flex flex-col">
                    <span class="font-bold">{{ d.expense.description }}</span>
                    <span class="text-slate-400 text-sm">Paid by: {{ d.expense.payer.name }}</span>
                    <span class="text-slate-400 text-sm">Your Share: ${{ "%.2f"|format(d.amount) }}</span>
                    <span class="text-slate-400 text-sm">Paid: ${{ "%.2f"|format(d.paid_amount) }} | Owed: ${{ "%.2f"|format(d.amount - d.paid_amount) }}</span>
                </li>
                {% endfor %}
            </ul>
        {% else %}
            <p class="text-slate-400">No expenses owed by you yet.</p>
        {% endif %}
    </div>
</div>
{% endblock %}
"""

# --- Jinja Environment Setup ---
jinja_env = Environment(loader=DictLoader({
    'layout.html': LAYOUT_TEMPLATE,
    'login.html': LOGIN_TEMPLATE,
    'dashboard.html': DASHBOARD_TEMPLATE,
    'friends.html': FRIENDS_TEMPLATE,
    'add_expense.html': ADD_EXPENSE_TEMPLATE,
    'settle.html': SETTLE_TEMPLATE,
    'index.html': HOME_PAGE_TEMPLATE,
    'past_expenses.html': PAST_EXPENSES_TEMPLATE
}))
jinja_env.globals.update(url_for=url_for, get_flashed_messages=get_flashed_messages)

def render_template(template_name, **context):
    template = jinja_env.get_template(template_name)
    if current_user.is_authenticated:
        context['current_user'] = current_user
    return template.render(context)

# --- Routes --- 

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated: return redirect(url_for('dashboard'))
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        if user and user.check_password(request.form['password']):
            login_user(user, remember=True)
            return redirect(url_for('dashboard'))
        flash('Invalid phone number or password.', 'error')
    return render_template('login.html', form_type='login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated: return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username')
        if User.query.filter_by(email=request.form['email']).first():
            flash('Phone number already in use.', 'error')
        elif username and User.query.filter_by(username=username).first():
            flash('Venmo username already taken.', 'error')
        else:
            new_user = User(
                name=request.form['name'],
                email=request.form['email'],
                username=username if username else None
            )
            new_user.set_password(request.form['password'])
            db.session.add(new_user)
            db.session.commit()
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('login'))
    return render_template('login.html', form_type='register')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

def calculate_balances():
    friendships = Friendship.query.filter(or_(Friendship.user1_id == current_user.id, Friendship.user2_id == current_user.id)).all()
    balances = {}
    friend_map = {}
    
    for fs in friendships:
        friend_id = fs.user2_id if fs.user1_id == current_user.id else fs.user1_id
        friend = User.query.get(friend_id)
        balances[friend] = 0
        friend_map[friend.id] = friend
    
    my_debts_to_friends = db.session.query(Debt).join(Expense).filter(
        Expense.payer_id.in_(friend_map.keys()),
        Debt.debtor_id == current_user.id
    ).all()
    
    debts_friends_owe_me = db.session.query(Debt).join(Expense).filter(
        Expense.payer_id == current_user.id,
        Debt.debtor_id.in_(friend_map.keys())
    ).all()

    for debt in my_debts_to_friends:
        friend = friend_map[debt.expense.payer_id]
        outstanding = debt.amount - debt.paid_amount
        if outstanding > 0:
            balances[friend] -= outstanding
            
    for debt in debts_friends_owe_me:
        friend = friend_map[debt.debtor_id]
        outstanding = debt.amount - debt.paid_amount
        if outstanding > 0:
            balances[friend] += outstanding
            
    return balances

@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/dashboard')
@login_required
def dashboard():
    balances = calculate_balances()
    request_count = FriendRequest.query.filter_by(receiver_id=current_user.id, status='pending').count()
    return render_template('dashboard.html', balances=balances, request_count=request_count)

@app.route('/friends')
@login_required
def friends():
    pending_requests = FriendRequest.query.filter_by(receiver_id=current_user.id, status='pending').all()
    requests_with_sender_info = [{'id': req.id, 'sender': User.query.get(req.sender_id)} for req in pending_requests]
    friendships = Friendship.query.filter(or_(Friendship.user1_id == current_user.id, Friendship.user2_id == current_user.id)).all()
    friend_list = [User.query.get(fs.user2_id if fs.user1_id == current_user.id else fs.user1_id) for fs in friendships]
    return render_template('friends.html', requests=requests_with_sender_info, friends=friend_list)

@app.route('/send_request/<int:user_id>')
@login_required
def send_request(user_id):
    found_user = User.query.get_or_404(user_id)
    if found_user.id == current_user.id:
        flash("You can't add yourself as a friend.", 'info')
    else:
        is_friend = Friendship.query.filter(or_(and_(Friendship.user1_id==current_user.id, Friendship.user2_id==found_user.id), and_(Friendship.user1_id==found_user.id, Friendship.user2_id==current_user.id))).first()
        is_pending = FriendRequest.query.filter(or_(and_(FriendRequest.sender_id==current_user.id, FriendRequest.receiver_id==found_user.id), and_(FriendRequest.sender_id==found_user.id, FriendRequest.receiver_id==current_user.id))).first()
        if is_friend: flash('You are already friends.', 'info')
        elif is_pending: flash('Friend request already pending.', 'info')
        else:
            new_request = FriendRequest(sender_id=current_user.id, receiver_id=found_user.id)
            db.session.add(new_request)
            db.session.commit()
            flash(f'Friend request sent to {found_user.name}.', 'success')
    return redirect(url_for('friends'))

@app.route('/handle_request/<int:request_id>/<action>')
@login_required
def handle_request(request_id, action):
    req = FriendRequest.query.get_or_404(request_id)
    if req.receiver_id != current_user.id:
        flash("You don't have permission for this request.", 'error')
        return redirect(url_for('friends'))

    if action == 'accept':
        friendship = Friendship(user1_id=req.sender_id, user2_id=req.receiver_id)
        db.session.add(friendship)
        flash(f'You are now friends with {User.query.get(req.sender_id).name}.', 'success')
    else:
        flash('Friend request declined.', 'info')
    
    db.session.delete(req)
    db.session.commit()
    return redirect(url_for('friends'))

@app.route('/add_expense', methods=['GET', 'POST'])
@login_required
def add_expense():
    friendships = Friendship.query.filter(or_(Friendship.user1_id == current_user.id, Friendship.user2_id == current_user.id)).all()
    friends_list = [User.query.get(fs.user2_id if fs.user1_id == current_user.id else fs.user1_id) for fs in friendships]

    if request.method == 'POST':
        total_amount = float(request.form['total_amount'])
        friend_ids = request.form.getlist('friend_ids')
        split_method = request.form.get('split_method', 'even')

        if not friend_ids:
            flash('You must select at least one friend to split with.', 'error')
            return redirect(url_for('add_expense'))

        new_expense = Expense(description=request.form['description'], total_amount=total_amount, payer_id=current_user.id)
        
        if split_method == 'even':
            amount_per_person = total_amount / (len(friend_ids) + 1)
            for friend_id in friend_ids:
                new_expense.debts.append(Debt(debtor_id=int(friend_id), amount=amount_per_person))
        else:
            total_custom_amount = 0
            for friend_id in friend_ids:
                amount_str = request.form.get(f'custom_amount_{friend_id}')
                if amount_str:
                    amount = float(amount_str)
                    total_custom_amount += amount
                    new_expense.debts.append(Debt(debtor_id=int(friend_id), amount=amount))
            
            if round(total_custom_amount, 2) > round(total_amount, 2):
                flash('Custom amounts cannot add up to more than the total bill.', 'error')
                return redirect(url_for('add_expense'))

        db.session.add(new_expense)
        db.session.commit()
        flash('Expense added successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('add_expense.html', friends=friends_list)
    
@app.route('/settle/<int:friend_id>', methods=['GET', 'POST'])
@login_required
def settle(friend_id):
    friend = User.query.get_or_404(friend_id)
    balances = calculate_balances()
    balance = balances.get(friend, 0)

    if balance <= 0:
        flash(f"You don't have an outstanding balance to settle with {friend.name}.", 'info')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        payment_amount = float(request.form['amount'])
        if payment_amount <= 0 or payment_amount > balance + 0.005:
            flash('Invalid settlement amount.', 'error')
            return redirect(url_for('settle', friend_id=friend.id))
        
        # Get all unpaid debts this friend owes the current user, oldest first
        unpaid_debts = db.session.query(Debt).join(Expense).filter(
            Expense.payer_id == current_user.id,
            Debt.debtor_id == friend.id,
            Debt.is_fully_paid == False
        ).order_by(Expense.id).all()

        remaining_payment = payment_amount
        for debt in unpaid_debts:
            if remaining_payment <= 0:
                break
            
            amount_owed = debt.amount - debt.paid_amount
            payment_for_this_debt = min(remaining_payment, amount_owed)
            
            debt.paid_amount += payment_for_this_debt
            remaining_payment -= payment_for_this_debt

            if abs(debt.amount - debt.paid_amount) < 0.005:
                debt.is_fully_paid = True
        
        db.session.commit()
        flash(f"You've recorded a ${payment_amount:.2f} payment from {friend.name}.", 'success')
        return redirect(url_for('dashboard'))

    return render_template('settle.html', friend=friend, balance=balance)

@app.route('/past_expenses')
@login_required
def past_expenses():
    # Expenses paid by the current user
    paid_expenses = Expense.query.filter_by(payer_id=current_user.id).order_by(Expense.id.desc()).all()
    # Debts where the current user is the debtor (owes someone else)
    owed_expenses = Debt.query.filter_by(debtor_id=current_user.id).join(Expense).order_by(Expense.id.desc()).all()
    return render_template('past_expenses.html', paid_expenses=paid_expenses, owed_expenses=owed_expenses)

# --- API Routes ---
@app.route('/api/search_users')
@login_required
def api_search_users():
    query = request.args.get('q', '')
    if len(query) < 2:
        return jsonify([])

    friend_ids = {f.user2_id if f.user1_id == current_user.id else f.user1_id for f in Friendship.query.filter(or_(Friendship.user1_id == current_user.id, Friendship.user2_id == current_user.id)).all()}
    pending_request_ids = {r.sender_id if r.receiver_id == current_user.id else r.receiver_id for r in FriendRequest.query.filter(or_(FriendRequest.sender_id == current_user.id, FriendRequest.receiver_id == current_user.id)).all()}
    
    exclude_ids = friend_ids.union(pending_request_ids).union({current_user.id})

    users = User.query.filter(
        User.username.ilike(f'%{query}%'),
        not_(User.id.in_(exclude_ids))
    ).limit(10).all()

    return jsonify([{'id': u.id, 'username': u.username, 'name': u.name} for u in users])

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=80, host='0.0.0.0') 
