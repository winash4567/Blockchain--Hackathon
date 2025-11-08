# Blockchain--Hackathon
Blockchain-based evidence ledger for T.N. Kaaval Hackathon 2025.

Kaaval Chain: A Blockchain-Based Evidence Ledger

A project for the Kaaval Hackathon, hosted by the Tamil Nadu Government.

Kaaval Chain is a secure, immutable, and auditable web application designed to solve the problem of maintaining the Chain of Custody for digital and physical evidence.

This prototype addresses the hackathon problem statement: "Blockchain-based chain-of-custody system for tamper-proof digital evidence."

The Problem

In a complex investigation, evidence passes through many hands (officers, departments, labs, and courts). Maintaining a verifiable log of "who touched what, and when" is a critical challenge. Traditional ledgers can be lost, altered, or tampered with.

Our Solution

Kaaval Chain solves this by using a private blockchain as a perfect, un-bribable witness.

Instead of trying to prevent actions, our system logs every action as a permanent, timestamped, and cryptographically signed block on the chain. It is impossible to edit or delete the past.

The UI provides a simple interface for officers, while the blockchain backend guarantees data integrity. The system's power is not in stopping a corrupt officer, but in creating an immutable record of their corruption, making it impossible to hide.

Core Features

Immutable Ledger: Built on a custom Python blockchain, every action (FIR, Evidence, Transfer) is a permanent block.

FIR-Based Case Model: All evidence and actions are logically linked to a primary FIR (First Information Report) block.

Role-Based Access Control:

SI (Sub-Inspector): Can register new FIRs, add evidence (physical or digital), and transfer case ownership.

Constable: Can view their department's cases and request access to others.

Judge: Has high-level read-only access to all cases and the complete, unfiltered audit log.

Digital Evidence Hashing: The app uses in-browser JavaScript (SHA-256) to hash uploaded files. It stores the hash (the "digital fingerprint") on-chain, not the file itself. This makes it possible to verify if the original file has been tampered with, even by one pixel.

Auditable Chain of Custody:

Access Grants: An SI can grant read-only access to another department, which is logged as an ACCESS_GRANT block.

Ownership Transfers: An SI can transfer full case ownership to another department, logged as a TRANSFER_OWNERSHIP block.

Case Visualization for Judiciary: A special "Case Mapper" tool for Judges to select any FIR and instantly see a clean, chronological timeline of every event in its history (creation, evidence added, grants, transfers).

How to Run This Project

Prerequisites

Python 3.x

Flask

Installation

Clone the repository:
git clone https://www.google.com/search?q=https://github.com/YOUR-USERNAME/kaaval-hackathon-project.git
cd kaaval-hackathon-project

Install Flask:
python -m pip install Flask

Run the application:
python main.py

Open your web browser and go to:
https://www.google.com/search?q=http://127.0.0.1:5000

Demo Flow & User Logins

Use these pre-set accounts to test the role-based features.
Password for all users: pass

Username: si_state
Role: SI
Department: State Police

Username: si_cyber
Role: SI
Department: Cyber Crime

Username: si_cbi
Role: SI
Department: CBI

Username: constable_state
Role: Constable
Department: State Police

Username: judge1
Role: Judge
Department: Judiciary

Demo: The "Indisputable Audit"

This demonstrates how the system catches tampering not with an alarm, but with a perfect log.

Login as si_state.

Register a new FIR (e.g., "Case-001").

Add an Evidence block to "Case-001" (e.g., upload a file to get its hash).

Logout.

Login as judge1.

You can see "Case-001."

Go to the "Case Mapper", select "Case-001," and see its simple history.

Logout.

Login as si_state (The "Culprit").

This officer wants to illicitly "lose" the case.

In the "Transfer Case Ownership" form on "Case-001," he transfers it to si_cbi in the CBI department.

Logout.

Login as judge1 (The "Detective").

Go to the "Case Mapper" and select "Case-001" again.

The timeline now shows:

FIR Registered by si_state.

Evidence Added by si_state.

Ownership Transferred by si_state to si_cbi.

The "tampering" (the illegitimate transfer) is permanently recorded, with the culprit's name (si_state) and the exact timestamp.
