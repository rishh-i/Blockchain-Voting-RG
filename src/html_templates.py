LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Login - Blockchain Voting System</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 400px; margin: 50px auto; padding: 20px; }
        .form-group { margin-bottom: 15px; }
        input[type="text"], input[type="password"] { width: 100%; padding: 8px; margin-top: 5px; }
        button { background-color: #007bff; color: white; padding: 10px 20px; border: none; cursor: pointer; }
        .error { color: red; margin-top: 10px; }
        .register-link { margin-top: 20px; text-align: center; }
    </style>
</head>
<body>
    <h2>Blockchain Voting System - Login</h2>
    <form method="POST">
        <div class="form-group">
            <label>Username:</label>
            <input type="text" name="username" required>
        </div>
        <div class="form-group">
            <label>Password:</label>
            <input type="password" name="password" required>
        </div>
        <button type="submit">Login</button>
    </form>
    {% if error %}
        <div class="error">{{ error }}</div>
    {% endif %}
    <div class="register-link">
        <a href="/register">Don't have an account? Register here</a>
    </div>
</body>
</html>
'''

REGISTER_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Register - Blockchain Voting System</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 400px; margin: 50px auto; padding: 20px; }
        .form-group { margin-bottom: 15px; }
        input[type="text"], input[type="password"], input[type="email"] { width: 100%; padding: 8px; margin-top: 5px; }
        button { background-color: #28a745; color: white; padding: 10px 20px; border: none; cursor: pointer; }
        .error { color: red; margin-top: 10px; }
        .login-link { margin-top: 20px; text-align: center; }
    </style>
</head>
<body>
    <h2>Blockchain Voting System - Register</h2>
    <form method="POST">
        <div class="form-group">
            <label>Username:</label>
            <input type="text" name="username" required>
        </div>
        <div class="form-group">
            <label>Email:</label>
            <input type="email" name="email" required>
        </div>
        <div class="form-group">
            <label>Password:</label>
            <input type="password" name="password" required>
        </div>
        <button type="submit">Register</button>
    </form>
    {% if error %}
        <div class="error">{{ error }}</div>
    {% endif %}
    <div class="login-link">
        <a href="/login">Already have an account? Login here</a>
    </div>
</body>
</html>
'''

DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Dashboard - Blockchain Voting System</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 20px auto; padding: 20px; }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }
        .election-card { border: 1px solid #ddd; padding: 20px; margin: 10px 0; border-radius: 5px; }
        .election-card h3 { margin-top: 0; }
        .btn { padding: 10px 15px; margin: 5px; text-decoration: none; border-radius: 3px; }
        .btn-primary { background-color: #007bff; color: white; }
        .btn-success { background-color: #28a745; color: white; }
        .btn-info { background-color: #17a2b8; color: white; }
        .btn-secondary { background-color: #6c757d; color: white; }
        .nav-links { margin-bottom: 20px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Blockchain Voting System</h1>
        <div>
            Welcome, {{ user.username }}! 
            <a href="/logout" class="btn btn-secondary">Logout</a>
        </div>
    </div>

    <div class="nav-links">
        <a href="/blockchain" class="btn btn-info">View Blockchain</a>
    </div>

    <h2>Available Elections</h2>

    {% for election in elections %}
        <div class="election-card">
            <h3>{{ election.title }}</h3>
            <p>{{ election.description }}</p>
            <p><strong>Start:</strong> {{ election.start_date }}</p>
            <p><strong>End:</strong> {{ election.end_date }}</p>
            <p><strong>Status:</strong> {{ "Active" if election.is_active else "Inactive" }}</p>

            <a href="/vote/{{ election.id }}" class="btn btn-primary">Vote</a>
            <a href="/results/{{ election.id }}" class="btn btn-success">View Results</a>
        </div>
    {% else %}
        <p>No elections available.</p>
    {% endfor %}
</body>
</html>
'''

VOTE_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Vote - Blockchain Voting System</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 600px; margin: 20px auto; padding: 20px; }
        .candidate-card { border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }
        .candidate-card:hover { background-color: #f8f9fa; }
        .vote-btn { background-color: #007bff; color: white; padding: 10px 20px; border: none; cursor: pointer; border-radius: 3px; }
        .back-link { margin-bottom: 20px; }
        .success { color: green; margin-top: 10px; }
        .error { color: red; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="back-link">
        <a href="/dashboard">← Back to Dashboard</a>
    </div>

    <h2>Cast Your Vote</h2>

    <form id="voteForm">
        <input type="hidden" name="election_id" value="{{ election_id }}">

        {% for candidate in candidates %}
            <div class="candidate-card">
                <h3>{{ candidate.name }}</h3>
                <p><strong>Party:</strong> {{ candidate.party }}</p>
                <p>{{ candidate.description }}</p>
                <button type="button" class="vote-btn" onclick="castVote({{ candidate.id }})">
                    Vote for {{ candidate.name }}
                </button>
            </div>
        {% endfor %}
    </form>

    <div id="message"></div>

    <script>
        function castVote(candidateId) {
            const formData = new FormData();
            formData.append('candidate_id', candidateId);
            formData.append('election_id', {{ election_id }});

            fetch('/cast_vote', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                const messageDiv = document.getElementById('message');
                if (data.success) {
                    messageDiv.innerHTML = '<div class="success">' + data.message + '</div>';
                    setTimeout(() => {
                        window.location.href = '/dashboard';
                    }, 2000);
                } else {
                    messageDiv.innerHTML = '<div class="error">' + data.error + '</div>';
                }
            })
            .catch(error => {
                document.getElementById('message').innerHTML = '<div class="error">Error casting vote</div>';
            });
        }
    </script>
</body>
</html>
'''

RESULTS_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Results - Blockchain Voting System</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 600px; margin: 20px auto; padding: 20px; }
        .result-card { border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }
        .vote-count { font-size: 24px; font-weight: bold; color: #007bff; }
        .back-link { margin-bottom: 20px; }
        .progress-bar { width: 100%; height: 20px; background-color: #e9ecef; border-radius: 10px; overflow: hidden; margin-top: 10px; }
        .progress-fill { height: 100%; background-color: #007bff; transition: width 0.3s ease; }
    </style>
</head>
<body>
    <div class="back-link">
        <a href="/dashboard">← Back to Dashboard</a>
    </div>

    <h2>Election Results</h2>

    {% set total_votes = results | sum(attribute='votes') %}

    {% for result in results %}
        <div class="result-card">
            <h3>{{ result.name }}</h3>
            <div class="vote-count">{{ result.votes }} votes</div>
            {% if total_votes > 0 %}
                {% set percentage = (result.votes / total_votes * 100) | round(1) %}
                <div>{{ percentage }}% of total votes</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {{ percentage }}%"></div>
                </div>
            {% endif %}
        </div>
    {% else %}
        <p>No votes cast yet.</p>
    {% endfor %}

    {% if total_votes > 0 %}
        <div style="margin-top: 30px; text-align: center;">
            <strong>Total Votes Cast: {{ total_votes }}</strong>
        </div>
    {% endif %}
</body>
</html>
'''

BLOCKCHAIN_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Blockchain - Blockchain Voting System</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 1000px; margin: 20px auto; padding: 20px; }
        .block-card { border: 2px solid #007bff; padding: 20px; margin: 15px 0; border-radius: 5px; background-color: #f8f9fa; }
        .block-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
        .block-hash { font-family: monospace; font-size: 12px; word-break: break-all; background-color: #e9ecef; padding: 5px; border-radius: 3px; }
        .vote-item { background-color: white; padding: 10px; margin: 5px 0; border-radius: 3px; border-left: 4px solid #28a745; }
        .back-link { margin-bottom: 20px; }
        .genesis-block { border-color: #ffc107; }
        .stats { display: flex; gap: 20px; margin-bottom: 20px; }
        .stat-card { background-color: #e9ecef; padding: 15px; border-radius: 5px; text-align: center; }
    </style>
</head>
<body>
    <div class="back-link">
        <a href="/dashboard">← Back to Dashboard</a>
    </div>

    <h2>Blockchain Explorer</h2>

    <div class="stats">
        <div class="stat-card">
            <h4>Total Blocks</h4>
            <div>{{ chain | length }}</div>
        </div>
        <div class="stat-card">
            <h4>Total Votes</h4>
            <div>{{ chain | sum(attribute='votes') | length }}</div>
        </div>
        <div class="stat-card">
            <h4>Chain Valid</h4>
            <div>✓ Valid</div>
        </div>
    </div>

    {% for block in chain %}
        <div class="block-card {% if block.index == 0 %}genesis-block{% endif %}">
            <div class="block-header">
                <h3>Block #{{ block.index }} {% if block.index == 0 %}(Genesis Block){% endif %}</h3>
                <span>{{ block.votes | length }} votes</span>
            </div>

            <div style="margin-bottom: 10px;">
                <strong>Timestamp:</strong> {{ block.timestamp | int | timestamp_to_date }}
            </div>

            <div style="margin-bottom: 10px;">
                <strong>Previous Hash:</strong>
                <div class="block-hash">{{ block.previous_hash }}</div>
            </div>

            <div style="margin-bottom: 10px;">
                <strong>Block Hash:</strong>
                <div class="block-hash">{{ block.hash }}</div>
            </div>

            <div style="margin-bottom: 10px;">
                <strong>Nonce:</strong> {{ block.nonce }}
            </div>

            {% if block.votes %}
                <div>
                    <strong>Votes in this block:</strong>
                    {% for vote in block.votes %}
                        <div class="vote-item">
                            <strong>Voter ID:</strong> {{ vote.voter_id }} | 
                            <strong>Candidate ID:</strong> {{ vote.candidate_id }} | 
                            <strong>Election ID:</strong> {{ vote.election_id }}
                            <div style="font-size: 12px; color: #666; margin-top: 5px;">
                                Vote Hash: {{ vote.vote_hash }}
                            </div>
                        </div>
                    {% endfor %}
                </div>
            {% endif %}
        </div>
    {% endfor %}

    <script>
        // Add timestamp formatting
        document.addEventListener('DOMContentLoaded', function() {
            const timestamps = document.querySelectorAll('[data-timestamp]');
            timestamps.forEach(function(element) {
                const timestamp = parseInt(element.getAttribute('data-timestamp'));
                const date = new Date(timestamp * 1000);
                element.textContent = date.toLocaleString();
            });
        });
    </script>
</body>
</html>
'''