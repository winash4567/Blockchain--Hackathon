# 🛡️ Kaaval Chain: Immutable Evidence Management System

**Kaaval Chain** is a blockchain-based digital ledger designed to maintain the Chain of Custody for forensic evidence. Built for the **T.N. Kaaval Hackathon 2025**, it solves the problem of evidence tampering by creating an immutable, decentralized record of every action taken by police officers and the judiciary.

---

## 🚀 Key Features

### 🔗 Core Blockchain
*   **Immutable Ledger:** Every FIR, evidence addition, and transfer is recorded as a block linked by cryptographic hashes (SHA-256).
*   **Data Persistence:** The blockchain state is automatically saved to disk (`chain_data.json`), ensuring data survives server restarts.
*   **Audit Trail:** Complete, unalterable history of who touched the evidence and when.

### 🌐 Decentralized Storage (Web3)
*   **IPFS Integration:** Digital evidence (images/docs) is uploaded to **IPFS** via Pinata.
*   **Tamper-Proof:** The blockchain stores the IPFS CID (Content Identifier). If the file is altered by even one pixel, the link becomes invalid.

### 🔫 Physical-to-Digital Bridge
*   **QR Code Generation:** Automatically generates QR codes for physical evidence (e.g., weapons).
*   **Instant Verification:** Scanning the QR code with a mobile device instantly loads the digital history of that specific item.

### 👥 Role-Based Access Control (RBAC)
*   **Sub-Inspector (SI):** Register FIRs, Add Evidence, Transfer Cases.
*   **Constable:** View Department cases, Request Access to other departments.
*   **Judge:** Full view of the Audit Log and Visual Case Mapping.

---

## 🛠️ Tech Stack

*   **Backend:** Python 3, Flask
*   **Blockchain Logic:** Custom Python implementation (SHA-256)
*   **Frontend:** HTML5, CSS3, JavaScript (CryptoJS for client-side hashing)
*   **Storage:** Local JSON (Ledger), Pinata IPFS (Files)
*   **Tools:** `qrcode` library, `urllib` (Standard Lib)

---

## ⚙️ Installation & Setup

### 1. Clone the Repository

### 2. Install Dependencies
You need Python installed. Run the following command to install the required lightweight libraries:

```bash
pip install Flask qrcode pillow
```
*(Note: IPFS logic uses Python's standard library, so no heavy requests library is needed).*

### 3. Configure Pinata (IPFS)
To enable file uploads, you need free API keys from Pinata.
1.  Sign up at [Pinata.cloud](https://www.pinata.cloud/).
2.  Go to **API Keys** -> **New Key** (Select Admin).
3.  Open `main.py` and find the configuration section:
    ```python
    # --- CONFIGURATION ---
    PINATA_API_KEY = "PASTE_YOUR_API_KEY_HERE"
    PINATA_SECRET_API_KEY = "PASTE_YOUR_SECRET_KEY_HERE"
    ```
4.  Paste your keys there.

### 4. Run the Application
```bash
python main.py
```
The application will start at `http://127.0.0.1:5000`.

---

## 🖥️ Usage Guide

### Login Credentials
The system comes pre-loaded with the following users for testing:

| Role | Username | Password | Department | Capabilities |
| :--- | :--- | :--- | :--- | :--- |
| **SI (Officer)** | `si_state` | `pass` | State Police | Create FIR, Add Evidence, Transfer |
| **Constable** | `constable_state` | `pass` | State Police | View Cases, Request Access |
| **SI (Cyber)** | `si_cyber` | `pass` | Cyber Crime | Create FIR (Cyber Dept) |
| **Judge** | `judge1` | `pass` | Judiciary | **Case Mapper**, Full Audit Log |

### Demo Workflow
1.  **Login as `si_state`**: Register a new FIR.
2.  **Add Evidence**:
    *   Select **Type: Document** -> Upload an image -> See the blue **IPFS Link** appear.
    *   Select **Type: Physical** -> Enter details -> See the **QR Code** appear.
3.  **Simulate Server Crash**: Stop the terminal (`Ctrl+C`) and restart it. Notice the data persists.
4.  **Login as `judge1`**: Go to **Case Mapper**, select the FIR, and view the chronological timeline.

---

## 📂 Project Structure

```text
kaaval-chain/
│
├── main.py                # Core application (Flask + Blockchain Engine)
├── chain_data.json        # Persistent ledger storage (Auto-generated)
├── templates/             # Frontend HTML files
│   ├── index.html         # Main Dashboard
│   ├── login.html         # Login Page
│   ├── inbox.html         # Notification Center
│   ├── case_mapper.html   # Judge's Search Tool
│   └── case_map_result.html # Visual Timeline
└── README.md              # Documentation
```
