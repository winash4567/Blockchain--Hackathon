import hashlib
import datetime
from flask import (
    Flask, render_template, request, redirect, url_for, flash, session, g
)
from functools import wraps

# --- 1. BLOCK & BLOCKCHAIN CLASSES (No changes) ---
class Block:
    def __init__(self, timestamp, data, previous_hash):
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.nonce = 0
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        hash_string = (
            str(self.timestamp)
            + str(self.data)
            + str(self.previous_hash)
            + str(self.nonce)
        )
        return hashlib.sha256(hash_string.encode()).hexdigest()

    def mine_block(self, difficulty):
        target = "0" * difficulty
        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()
        print(f"Block Mined! Hash: {self.hash}")

class Blockchain:
    def __init__(self):
        self.chain = []
        self.difficulty = 2 # Keep low for fast demo
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis_block = Block(datetime.datetime.now(), {"block_type": "GENESIS"}, "0")
        genesis_block.mine_block(self.difficulty)
        self.chain.append(genesis_block)

    def get_latest_block(self):
        return self.chain[-1]

    def add_block(self, data):
        previous_hash = self.get_latest_block().hash
        new_block = Block(datetime.datetime.now(), data, previous_hash)
        new_block.mine_block(self.difficulty)
        self.chain.append(new_block)

# --- 3. FLASK WEB APP & USER MANAGEMENT (No changes) ---

app = Flask(__name__)
app.config['SECRET_KEY'] = 'my_super_secret_hackathon_key_12345'

evidence_chain = Blockchain()
MESSAGES = [] 

USERS = {
    "si_state": {"password": "pass", "role": "SI", "department": "State Police"},
    "constable_state": {"password": "pass", "role": "Constable", "department": "State Police"},
    "si_cyber": {"password": "pass", "role": "SI", "department": "Cyber Crime"},
    "constable_cyber": {"password": "pass", "role": "Constable", "department": "Cyber Crime"},
    "si_cbi": {"password": "pass", "role": "SI", "department": "CBI"},
    "constable_cbi": {"password": "pass", "role": "Constable", "department": "CBI"},
    "judge1": {"password": "pass", "role": "Judge", "department": "Judiciary"}
}
ALL_DEPARTMENTS = ["State Police", "Cyber Crime", "CBI", "Judiciary"]

def role_required(allowed_roles):
    def decorator(f):
        @wraps(f)
        def wrap(*args, **kwargs):
            if 'role' not in session:
                flash("You must be logged in to view this page.", 'danger')
                return redirect(url_for('login'))
            if session['role'] not in allowed_roles:
                flash("You do not have permission to access this feature.", 'danger')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return wrap
    return decorator

@app.before_request
def load_logged_in_user():
    username = session.get('username')
    if username is None:
        g.user = None
        g.inbox_count = 0
    else:
        g.user = {
            "username": username,
            "role": session.get('role'),
            "department": session.get('department')
        }
        count = 0
        for msg in MESSAGES:
            if msg['owner_username'] == username:
                count += 1
        g.inbox_count = count
    
    g.all_departments = [dept for dept in ALL_DEPARTMENTS if dept != session.get('department')]


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        department = request.form['department']
        user = USERS.get(username)
        if user and user['password'] == password and user['department'] == department:
            session.clear()
            session['username'] = username
            session['role'] = user['role']
            session['department'] = user['department']
            flash(f"Welcome, {user['role']} {username}!", 'success')
            return redirect(url_for('index'))
        else:
            flash("Invalid credentials or department.", 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", 'success')
    return redirect(url_for('login'))

@app.route('/inbox')
@role_required(allowed_roles=['SI', 'Constable', 'Judge'])
def inbox():
    my_messages_with_index = []
    for i, msg in reversed(list(enumerate(MESSAGES))):
        if msg['owner_username'] == session['username']:
            my_messages_with_index.append({'message': msg, 'original_index': i})
    return render_template('inbox.html', messages_with_index=my_messages_with_index)

# --- 4. CORE APPLICATION LOGIC (FIR-BASED MODEL) ---

def get_current_chain_state():
    """
    (This is the "Brain" - Unchanged from last version)
    """
    fir_state = {} 
    all_evidence_blocks = []
    all_grant_blocks = []
    all_transfer_blocks = []
    on_chain_grants = set()

    # PASS 1: Find all FIRs
    for i, block in enumerate(evidence_chain.chain):
        block_type = block.data.get("block_type")
        if block_type == "FIR":
            fir_state[block.hash] = {
                'fir_block': block,
                'index': i,
                'evidence': [],
                'current_owner_dept': block.data['department'],
                'current_owner_username': block.data['owner'],
                'grants': set(),
                'is_pending': set(),
            }

    # PASS 2: Link Evidence, Grants, and Transfers
    for block in evidence_chain.chain:
        block_type = block.data.get("block_type")
        
        if block_type == "EVIDENCE":
            all_evidence_blocks.append(block)
            try:
                linked_fir_hash = block.data.get('linked_fir_hash')
                if linked_fir_hash in fir_state:
                    fir_state[linked_fir_hash]['evidence'].append(block)
            except KeyError: pass
        
        elif block_type == "ACCESS_GRANT":
            all_grant_blocks.append(block)
            try:
                fir_hash = block.data['fir_hash']
                if fir_hash in fir_state:
                    fir_state[fir_hash]['grants'].add(block.data['requester_dept'])
            except KeyError: pass

        elif block_type == "TRANSFER_OWNERSHIP":
            all_transfer_blocks.append(block)
            try:
                fir_hash = block.data['fir_hash']
                if fir_hash in fir_state:
                    fir_state[fir_hash]['current_owner_dept'] = block.data['new_dept']
                    fir_state[fir_hash]['current_owner_username'] = block.data['new_officer_username']
            except KeyError: pass
            
    # PASS 3: Populate pending (off-chain) requests
    for msg in MESSAGES:
        try:
            fir_hash = msg['fir_hash']
            if fir_hash in fir_state:
                fir_state[fir_hash]['is_pending'].add(msg['requester_info']['department'])
        except KeyError: pass
                
    return fir_state, all_evidence_blocks, all_grant_blocks, all_transfer_blocks


@app.route('/')
@role_required(allowed_roles=['Constable', 'SI', 'Judge'])
def index():
    # Get the final, current state of the entire chain
    fir_state, all_evidence_blocks, all_grant_blocks, all_transfer_blocks = get_current_chain_state()

    visible_firs = []
    other_firs = []
    
    current_dept = session.get('department')
    current_role = session.get('role')

    if current_role == 'Judge':
        # Judges see all FIRs
        visible_firs = [state for state in fir_state.values()]
    
    else:
        # Filter for police roles
        for state in fir_state.values():
            is_my_dept = state['current_owner_dept'] == current_dept
            has_grant = current_dept in state['grants']

            if is_my_dept or has_grant:
                state['granted_access'] = has_grant and not is_my_dept
                visible_firs.append(state)
            else:
                state['request_is_pending'] = current_dept in state['is_pending']
                other_firs.append(state)

    # *** THIS IS THE FIX ***
    # The template needs 'fir_state' for the audit log,
    # so we must pass it in.
    return render_template(
        'index.html', 
        visible_firs=visible_firs, 
        other_firs=other_firs,
        all_evidence_blocks=all_evidence_blocks,
        all_grant_blocks=all_grant_blocks,
        all_transfer_blocks=all_transfer_blocks,
        fir_state=fir_state  # <-- THE MISSING PIECE
    )

# --- 5. SI ROUTES (Unchanged) ---

@app.route('/register_fir', methods=['POST'])
@role_required(allowed_roles=['SI'])
def register_fir_route():
    if request.method == 'POST':
        case_id = request.form.get('case_id')
        if not case_id:
            flash("Case ID / FIR Number is required!", 'danger')
            return redirect(url_for('index'))
        fir_data = {
            "block_type": "FIR",
            "Case ID": case_id,
            "Complainant": request.form.get('complainant'),
            "Sections": request.form.get('sections'),
            "Location": request.form.get('location'),
            "Notes": request.form.get('notes'),
            "department": session['department'],
            "owner": session['username']
        }
        evidence_chain.add_block(fir_data)
        flash("New FIR registered successfully on the blockchain!", 'success')
    return redirect(url_for('index'))


@app.route('/add_evidence', methods=['POST'])
@role_required(allowed_roles=['SI'])
def add_evidence_route():
    if request.method == 'POST':
        linked_fir_hash = request.form.get('linked_fir_hash')
        description = request.form.get('description')
        if not linked_fir_hash or not description:
            flash("You must select an FIR and provide an evidence description/hash!", 'danger')
            return redirect(url_for('index'))
        evidence_data = {
            "block_type": "EVIDENCE",
            "linked_fir_hash": linked_fir_hash,
            "Evidence Type": request.form.get('evidence_type'),
            "Evidence File/Description": description,
            "Collecting Officer": request.form.get('officer_name'),
            "Storage Location": request.form.get('storage_location'),
            "Notes": request.form.get('notes'),
            "added_by_dept": session['department'],
            "added_by_user": session['username']
        }
        evidence_chain.add_block(evidence_data)
        flash("New evidence block linked to FIR successfully!", 'success')
    return redirect(url_for('index'))


@app.route('/request_access/<string:fir_hash>', methods=['POST'])
@role_required(allowed_roles=['SI', 'Constable'])
def request_access(fir_hash):
    try:
        fir_state, _, _, _ = get_current_chain_state()
        if fir_hash not in fir_state:
             flash("Cannot request access: This FIR is not valid.", 'danger')
             return redirect(url_for('index'))
        current_owner_username = fir_state[fir_hash]['current_owner_username']
        new_request = {
            "owner_username": current_owner_username,
            "fir_hash": fir_hash,
            "fir_case_id": fir_state[fir_hash]['fir_block'].data.get('Case ID'),
            "requester_info": g.user
        }
        MESSAGES.append(new_request)
        flash(f"Access requested for Case ID: {new_request['fir_case_id']}", 'success')
    except Exception as e:
        flash(f"Error requesting access: {e}", 'danger')
    return redirect(url_for('index'))


@app.route('/approve_request/<int:msg_index>', methods=['POST'])
@role_required(allowed_roles=['SI'])
def approve_request(msg_index):
    try:
        msg = MESSAGES.pop(msg_index)
        grant_data = {
            "block_type": "ACCESS_GRANT",
            "fir_hash": msg['fir_hash'],
            "case_id": msg['fir_case_id'],
            "requester_dept": msg['requester_info']['department'],
            "requester_username": msg['requester_info']['username'],
            "granter_username": g.user['username'],
            "granter_dept": g.user['department']
        }
        evidence_chain.add_block(grant_data)
        flash(f"Access granted to {msg['requester_info']['department']}. Grant is now on the blockchain.", 'success')
    except Exception as e:
        flash(f"An error occurred: {e}", 'danger')
    return redirect(url_for('inbox'))


@app.route('/transfer_case/<string:fir_hash>', methods=['POST'])
@role_required(allowed_roles=['SI'])
def transfer_case(fir_hash):
    try:
        new_dept = request.form.get('new_dept')
        new_officer_username = request.form.get('new_officer_username')
        if not new_dept or not new_officer_username:
            flash("New department and officer username are required.", 'danger')
            return redirect(url_for('index'))
        fir_state, _, _, _ = get_current_chain_state()
        if fir_hash not in fir_state:
             flash("Cannot transfer: This FIR is not valid.", 'danger')
             return redirect(url_for('index'))
        state = fir_state[fir_hash]
        if state['current_owner_dept'] != session['department']:
            flash("You are not the current owner and cannot transfer this case.", 'danger')
            return redirect(url_for('index'))
        transfer_data = {
            "block_type": "TRANSFER_OWNERSHIP",
            "fir_hash": fir_hash,
            "case_id": state['fir_block'].data.get('Case ID'),
            "previous_dept": session['department'],
            "previous_officer_username": session['username'],
            "new_dept": new_dept,
            "new_officer_username": new_officer_username
        }
        evidence_chain.add_block(transfer_data)
        flash(f"Case ID {state['fir_block'].data.get('Case ID')} has been transferred to {new_dept}.", 'success')
    except Exception as e:
        flash(f"An error occurred during transfer: {e}", 'danger')
    return redirect(url_for('index'))


# --- 6. NEW: JUDGE'S CASE MAPPER ROUTES ---

@app.route('/case_mapper')
@role_required(allowed_roles=['Judge'])
def case_mapper():
    """
    (Unchanged)
    Shows the "Chooser" page. Gets all FIRs so the
    Judge can pick one from a dropdown.
    """
    fir_state, _, _, _ = get_current_chain_state()
    # Pass the full state dictionary, the template will loop through it
    return render_template('case_mapper.html', fir_state=fir_state)


@app.route('/case_map_result')
@role_required(allowed_roles=['Judge'])
def case_map_result():
    """
    (Unchanged)
    This is the "tree" page. It finds all blocks for
    ONE FIR and sorts them by time.
    """
    fir_hash = request.args.get('fir_hash')
    if not fir_hash:
        flash("You must select an FIR to map.", 'danger')
        return redirect(url_for('case_mapper'))
        
    # Find the main FIR block
    fir_block = None
    for block in evidence_chain.chain:
        if block.hash == fir_hash and block.data.get('block_type') == 'FIR':
            fir_block = block
            break
            
    if not fir_block:
        flash("Invalid FIR selected.", 'danger')
        return redirect(url_for('case_mapper'))
        
    # Now find all related blocks
    event_list = []
    for block in evidence_chain.chain:
        # Check if the block is linked by the fir_hash
        if block.data.get('linked_fir_hash') == fir_hash: # Evidence
            event_list.append(block)
        elif block.data.get('fir_hash') == fir_hash: # Grant or Transfer
            event_list.append(block)
            
    # Sort the events by their timestamp to create the timeline
    try:
        event_list.sort(key=lambda x: x.timestamp)
    except Exception as e:
        print(f"Error sorting: {e}") 

    return render_template(
        'case_map_result.html', 
        fir_block=fir_block,
        event_list=event_list
    )


# --- 7. RUN THE APP ---
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
