# Divy - Effortless Expense Sharing

<p align="center">
  <img src="https://storage.googleapis.com/gemini-prod-us-central1-8298/images/5f04b2c1-229d-4034-8b65-64f3d2f26038.svg" alt="Divy Logo" width="150">
</p>

<h3 align="center">Stop splitting hairs. Start splitting bills.</h3>

<p align="center">
  <a href="#about">About</a> •
  <a href="#key-features">Features</a> •
  <a href="#tech-stack">Tech Stack</a> •
  <a href="#setup--installation">Installation</a> •
  <a href="#how-to-run">Running the App</a>
</p>

---

## About The Project

**Divy** is a full-stack web application designed to take the headache out of sharing expenses with friends. From group dinners to shared subscriptions, Divy provides a clear, real-time view of who owes who, eliminating awkward conversations and manual calculations.

Built with a clean Python and Flask backend, Divy allows users to create accounts, manage friendships, log expenses with complex splits, and settle up balances with partial or full payments. It's the simplest way to keep your social life and your finances in perfect balance.

## Key Features

* **Secure User Accounts:** Full registration and login system with password hashing.
* **Friend Management System:** Users can search for friends by a unique Venmo username and manage friend requests.
* **Dynamic Expense Splitting:**
    * Log expenses and split them with multiple friends at once.
    * Choose between splitting the bill **evenly** or specifying **custom amounts** for each person.
* **Real-Time Balance Dashboard:** A clear, at-a-glance view of who you owe and who owes you, updated instantly.
* **Partial & Full Settlements:** Record payments from friends to settle debts. The system intelligently applies payments to the oldest debts first and handles both partial and full payments.
* **Live User Search:** An asynchronous search feature to find and add new friends without page reloads.

## Tech Stack

* **Backend:** Python with [Flask](https://flask.palletsprojects.com/)
* **Database:** [Flask-SQLAlchemy](https://flask-sqlalchemy.palletsprojects.com/) with SQLite
* **Authentication:** [Flask-Login](https://flask-login.readthedocs.io/) for session management.
* **Frontend:** HTML5 with [Tailwind CSS](https://tailwindcss.com/) for styling.
* **Animations:** [AOS (Animate on Scroll)](https://michalsnik.github.io/aos/) for the landing page.

## Setup & Installation

Follow these steps to get a local copy up and running.

### Prerequisites

* Python 3.x
* `pip` (Python package installer)

### Installation

1.  **Clone the repo**
    ```sh
    git clone [https://github.com/your_username/divy.git](https://github.com/your_username/divy.git)
    cd divy
    ```
2.  **Create a virtual environment (recommended)**
    ```sh
    # For Windows
    python -m venv venv
    venv\Scripts\activate

    # For macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```
3.  **Install Python packages**
    ```sh
    pip install Flask Flask-SQLAlchemy Flask-Login Werkzeug
    ```
4.  **Delete any old database file (if applicable)**
    If you are re-installing or have an old version, make sure to delete the `instance/splittr_app_v2.db` file to ensure the new database schema is created correctly.

## How to Run

1.  **Run the Flask application** from the root directory of the project:
    ```sh
    python app.py
    ```
2.  **Open your browser** and navigate to:
    ```
    [http://127.0.0.1:5000](http://127.0.0.1:5000)
    ```
The application will automatically create the `instance/splittr_app_v2.db` SQLite database file on its first run. You can now register a few test accounts, add them as friends, and start splitting expenses!
