from ecdsa import SigningKey, SECP256k1
import qrcode
import io
import base64
import hashlib
import datetime
import json
import os
import urllib.request
import urllib.error
import uuid
from flask import (
    Flask, render_template, request, redirect, url_for, flash, session, g
)
from functools import wraps

# --- CONFIGURATION ---
# Enter your Pinata Keys here. If you don't have them, keep these strings.
PINATA_API_KEY = "c15b7a8a074b9f55d898"
PINATA_SECRET_API_KEY = "b53ad5d95ecebd5ae7c4dcaaad958e7c48d03616993bf592aee70b4571eec8b3"

# --- HELPER: UPLOAD TO IPFS (No 'requests' library needed) ---
def upload_to_ipfs(file_obj):
    """Uploads a file to IPFS via Pinata using standard Python libraries."""
    url = "https://api.pinata.cloud/pinning/pinFileToIPFS"
    boundary = str(uuid.uuid4())
    
    try:
        file_data = file_obj.read()
        filename = file_obj.filename
        content_type = file_obj.content_type or 'application/octet-stream'

        # Construct Multipart Body
        body = []
        body.append(f'--{boundary}'.encode('utf-8'))
        body.append(f'Content-Disposition: form-data; name="file"; filename="{filename}"'.encode('utf-8'))
        body.append(f'Content-Type: {content_type}'.encode('utf-8'))
        body.append(b'')
        body.append(file_data)
        body.append(f'--{boundary}--'.encode('utf-8'))
        body.append(b'')
        body_bytes = b'\r\n'.join(body)

        req = urllib.request.Request(url, data=body_bytes)
        req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
        req.add_header('pinata_api_key', PINATA_API_KEY)
        req.add_header('pinata_secret_api_key', PINATA_SECRET_API_KEY)

        print(f"Uploading {filename} to IPFS...")
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read())
            print(f"IPFS Success! CID: {data['IpfsHash']}")
            return data['IpfsHash']
    except Exception as e:
        print(f"IPFS Upload Failed: {e}")
        return None

# --- 1. BLOCK & BLOCKCHAIN CLASSES (With Persistence) ---
class Block:
    def __init__(self, timestamp, data, previous_hash):
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.nonce = 0
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        hash_string = (
            str(self.timestamp) + str(self.data) + str(self.previous_hash) + str(self.nonce)
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
        self.difficulty = 2
        self.filename = 'chain_data.json' # File name

        # Attempt to load existing chain
        if not self.load_chain():
            print("No existing chain found. Creating Genesis Block.")
            self.create_genesis_block()
        else:
            print(f"Loaded existing chain with {len(self.chain)} blocks.")

    def create_genesis_block(self):
        genesis_block = Block(datetime.datetime.now(), {"block_type": "GENESIS"}, "0")
        genesis_block.mine_block(self.difficulty)
        self.chain.append(genesis_block)
        self.save_chain()

    def get_latest_block(self):
        return self.chain[-1]

    def add_block(self, data):
        previous_hash = self.get_latest_block().hash
        new_block = Block(datetime.datetime.now(), data, previous_hash)
        new_block.mine_block(self.difficulty)
        self.chain.append(new_block)
        self.save_chain()

    def save_chain(self):
        """Saves chain to JSON file"""
        chain_data = []
        for block in self.chain:
            b_dict = block.__dict__.copy()
            b_dict['timestamp'] = block.timestamp.isoformat()
            chain_data.append(b_dict)
        
        # Save to current working directory
        with open(self.filename, 'w') as f:
            json.dump(chain_data, f, indent=4)
        print(f"Blockchain saved to {os.path.abspath(self.filename)}")

    def load_chain(self):
        """Loads chain from JSON file"""
        if not os.path.exists(self.filename):
            return False
        try:
            with open(self.filename, 'r') as f:
                chain_data = json.load(f)
            self.chain = []
            for b_dict in chain_data:
                ts = datetime.datetime.fromisoformat(b_dict['timestamp'])
                block = Block(ts, b_dict['data'], b_dict['previous_hash'])
                block.nonce = b_dict['nonce']
                block.hash = b_dict['hash']
                self.chain.append(block)
            return True
        except Exception as e:
            print(f"Error loading chain: {e}")
            return False

# --- 3. FLASK WEB APP ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'kaaval_hackathon_secret_key'

# Initialize Blockchain
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
USER_KEYS = {}

print("--- Generating Digital Identity Keys ---")
for username in USERS:
    # Generate a new Private Key (Signing Key)
    sk = SigningKey.generate(curve=SECP256k1)
    # Derive the Public Key (Verifying Key)
    vk = sk.verifying_key
    
    USER_KEYS[username] = {
        'private': sk,
        'public': vk.to_string().hex() # Convert to string for storage
    }
    print(f"User: {username} | Public Key: {USER_KEYS[username]['public'][:20]}...")

def sign_block_data(data_dict, username):
    """
    Takes the block data, converts to string, and signs it with user's Private Key.
    Returns the Hex Signature.
    """
    try:
        private_key = USER_KEYS[username]['private']
        # Convert dictionary to stable string
        message = json.dumps(data_dict, sort_keys=True).encode()
        signature = private_key.sign(message).hex()
        return signature
    except KeyError:
        return "ERROR_NO_KEY"
    
ALL_DEPARTMENTS = ["State Police", "Cyber Crime", "CBI", "Judiciary"]

def role_required(allowed_roles):
    def decorator(f):
        @wraps(f)
        def wrap(*args, **kwargs):
            if 'role' not in session:
                return redirect(url_for('login'))
            if session['role'] not in allowed_roles:
                flash("Permission denied.", 'danger')
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
        g.user = {"username": username, "role": session.get('role'), "department": session.get('department')}
        count = sum(1 for msg in MESSAGES if msg['owner_username'] == username)
        g.inbox_count = count
    g.all_departments = [dept for dept in ALL_DEPARTMENTS if dept != session.get('department')]

# --- ROUTES ---
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
            return redirect(url_for('index'))
        else:
            flash("Invalid credentials.", 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/inbox')
@role_required(allowed_roles=['SI', 'Constable', 'Judge'])
def inbox():
    my_msgs = [{'message': msg, 'original_index': i} for i, msg in reversed(list(enumerate(MESSAGES))) if msg['owner_username'] == session['username']]
    return render_template('inbox.html', messages_with_index=my_msgs)

def get_current_chain_state():
    fir_state = {} 
    all_evidence = []
    all_grants = []
    all_transfers = []

    for i, block in enumerate(evidence_chain.chain):
        bt = block.data.get("block_type")
        if bt == "FIR":
            fir_state[block.hash] = {
                'fir_block': block, 'index': i, 'evidence': [],
                'current_owner_dept': block.data['department'],
                'current_owner_username': block.data['owner'],
                'grants': set(), 'is_pending': set(),
            }

    for block in evidence_chain.chain:
        bt = block.data.get("block_type")
        if bt == "EVIDENCE":
            all_evidence.append(block)
            if block.data.get('linked_fir_hash') in fir_state:
                fir_state[block.data['linked_fir_hash']]['evidence'].append(block)
        elif bt == "ACCESS_GRANT":
            all_grants.append(block)
            if block.data.get('fir_hash') in fir_state:
                fir_state[block.data['fir_hash']]['grants'].add(block.data['requester_dept'])
        elif bt == "TRANSFER_OWNERSHIP":
            all_transfers.append(block)
            if block.data.get('fir_hash') in fir_state:
                s = fir_state[block.data['fir_hash']]
                s['current_owner_dept'] = block.data['new_dept']
                s['current_owner_username'] = block.data['new_officer_username']

    for msg in MESSAGES:
        if msg.get('fir_hash') in fir_state:
            fir_state[msg['fir_hash']]['is_pending'].add(msg['requester_info']['department'])
                
    return fir_state, all_evidence, all_grants, all_transfers

@app.route('/')
@role_required(allowed_roles=['Constable', 'SI', 'Judge'])
def index():
    fir_state, all_evidence, all_grants, all_transfers = get_current_chain_state()
    visible_firs = []
    other_firs = []
    
    dept = session.get('department')
    role = session.get('role')

    if role == 'Judge':
        visible_firs = list(fir_state.values())
    else:
        for state in fir_state.values():
            is_my_dept = state['current_owner_dept'] == dept
            has_grant = dept in state['grants']
            if is_my_dept or has_grant:
                state['granted_access'] = has_grant and not is_my_dept
                visible_firs.append(state)
            else:
                state['request_is_pending'] = dept in state['is_pending']
                other_firs.append(state)

    return render_template(
        'index.html', visible_firs=visible_firs, other_firs=other_firs,
        all_evidence_blocks=all_evidence, all_grant_blocks=all_grants,
        all_transfer_blocks=all_transfers, fir_state=fir_state
    )

@app.route('/register_fir', methods=['POST'])
@role_required(allowed_roles=['SI'])
def register_fir_route():
    # 1. Prepare Data
    block_data = {
        "block_type": "FIR",
        "Case ID": request.form.get('case_id'),
        "Complainant": request.form.get('complainant'),
        "Sections": request.form.get('sections'),
        "Location": request.form.get('location'),
        "Notes": request.form.get('notes'),
        "department": session['department'],
        "owner": session['username']
    }
    
    # 2. DIGITAL SIGNATURE (New)
    # Sign the data using the logged-in user's Private Key
    signature = sign_block_data(block_data, session['username'])
    public_key = USER_KEYS[session['username']]['public']
    
    # 3. Attach Signature to Block
    block_data['digital_signature'] = signature
    block_data['signer_public_key'] = public_key
    
    # 4. Add to Blockchain
    evidence_chain.add_block(block_data)
    
    flash("New FIR registered & Digitally Signed!", 'success')
    return redirect(url_for('index'))

@app.route('/add_evidence', methods=['POST'])
@role_required(allowed_roles=['SI'])
def add_evidence_route():
    # 1. Handle IPFS Upload
    ipfs_cid = "Not Uploaded (Physical/Other)"
    file = request.files.get('evidence_file')
    if file and file.filename != '':
        res = upload_to_ipfs(file)
        if res: ipfs_cid = res

    # 2. GENERATE QR CODE (If Physical)
    qr_code_base64 = None
    ev_type = request.form.get('evidence_type')
    linked_hash = request.form.get('linked_fir_hash')

    if ev_type == "Physical":
        # Create the URL that the QR code will point to
        # It points to the Case Timeline for this specific FIR
        # _external=True creates a full URL (http://192.168.../...)
        target_url = url_for('case_map_result', fir_hash=linked_hash, _external=True)
        
        # Generate the QR Image
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(target_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert image to Base64 string to store in JSON
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        qr_code_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

    # 3. Add to Chain
    evidence_chain.add_block({
        "block_type": "EVIDENCE",
        "linked_fir_hash": linked_hash,
        "Evidence Type": ev_type,
        "Evidence File/Description": request.form.get('description'),
        "IPFS CID": ipfs_cid,
        "QR Label": qr_code_base64,  # <--- NEW FIELD
        "Collecting Officer": request.form.get('officer_name'),
        "Storage Location": request.form.get('storage_location'),
        "Notes": request.form.get('notes'),
        "added_by_dept": session['department'],
        "added_by_user": session['username']
    })
    flash("Evidence added to blockchain!", 'success')
    return redirect(url_for('index'))

@app.route('/request_access/<string:fir_hash>', methods=['POST'])
@role_required(allowed_roles=['SI', 'Constable'])
def request_access(fir_hash):
    fir_state, _, _, _ = get_current_chain_state()
    if fir_hash in fir_state:
        MESSAGES.append({
            "owner_username": fir_state[fir_hash]['current_owner_username'],
            "fir_hash": fir_hash,
            "fir_case_id": fir_state[fir_hash]['fir_block'].data.get('Case ID'),
            "requester_info": g.user
        })
        flash("Access requested.", 'success')
    return redirect(url_for('index'))

@app.route('/approve_request/<int:msg_index>', methods=['POST'])
@role_required(allowed_roles=['SI'])
def approve_request(msg_index):
    try:
        msg = MESSAGES.pop(msg_index)
        evidence_chain.add_block({
            "block_type": "ACCESS_GRANT",
            "fir_hash": msg['fir_hash'],
            "case_id": msg['fir_case_id'],
            "requester_dept": msg['requester_info']['department'],
            "requester_username": msg['requester_info']['username'],
            "granter_username": g.user['username'],
            "granter_dept": g.user['department']
        })
        flash("Access granted.", 'success')
    except: pass
    return redirect(url_for('inbox'))

@app.route('/transfer_case/<string:fir_hash>', methods=['POST'])
@role_required(allowed_roles=['SI'])
def transfer_case(fir_hash):
    fir_state, _, _, _ = get_current_chain_state()
    if fir_hash in fir_state:
        evidence_chain.add_block({
            "block_type": "TRANSFER_OWNERSHIP",
            "fir_hash": fir_hash,
            "case_id": fir_state[fir_hash]['fir_block'].data.get('Case ID'),
            "previous_dept": session['department'],
            "previous_officer_username": session['username'],
            "new_dept": request.form.get('new_dept'),
            "new_officer_username": request.form.get('new_officer_username')
        })
        flash("Case transferred.", 'success')
    return redirect(url_for('index'))

@app.route('/case_mapper')
@role_required(allowed_roles=['Judge'])
def case_mapper():
    fir_state, _, _, _ = get_current_chain_state()
    return render_template('case_mapper.html', fir_state=fir_state)

@app.route('/case_map_result')
@role_required(allowed_roles=['Judge'])
def case_map_result():
    fir_hash = request.args.get('fir_hash')
    fir_block = None
    event_list = []
    
    # Simple search
    for block in evidence_chain.chain:
        if block.hash == fir_hash and block.data.get('block_type') == 'FIR':
            fir_block = block
        if block.data.get('linked_fir_hash') == fir_hash or block.data.get('fir_hash') == fir_hash:
            event_list.append(block)
            
    event_list.sort(key=lambda x: x.timestamp)
    return render_template('case_map_result.html', fir_block=fir_block, event_list=event_list)

if __name__ == '__main__':
    # Print current directory to help find the JSON file
    print(f"Server starting...")
    print(f"Working Directory: {os.getcwd()}")
    app.run(debug=True, host='0.0.0.0', port=5000)