# Zytherion Blockchain

Zytherion is a hybrid Layer-1 blockchain that combines **Proof of Work (PoW)** and **Proof of Stake (PoS)** consensus mechanisms.  
It’s designed for high-performance decentralized applications, integrating **AI-powered validation** for enhanced security and efficiency.

---

##  Key Features

- ⚡ **Hybrid Consensus** — Combines PoW and PoS for balanced energy efficiency and security.  
- 🧠 **AI Validator** — Machine learning validator using TensorFlow to analyze and optimize consensus participation.  
- 🔗 **Modular Architecture** — Core written in **Rust**, node layer in **Go**, and AI validation powered by **Python**.  
- 🧩 **WASM Compatible** — Supports smart contract execution via WebAssembly (WASM).  
- 🌐 **P2P Network** — Secure peer-to-peer networking for decentralized communication.  
- 📊 **Grafana Integration** — Real-time node monitoring and blockchain analytics dashboard.

---

## ⚙️ Installation & Setup

### 1️. Clone the Repository
```bash
git clone https://github.com/zhao-leihan/Zytherion-Blockchain.git
cd Zytherion-Blockchain
```

### 2️. Build Core Components
##### Rust (Core)

```bash
cd core
cargo build --release
```

##### Go (Node)

```bash
cd ../node
go build -o zytherion-node.exe .
```

##### Python (AI Validator)

```bash
cd ../ai-validator
pip install -r requirements.txt
```

### 3. Running Zytherion Node
#### Start a Zytherion node:

```bash
Copy code
./zytherion-node.exe start
```

#### Optional flags:
```Bash
--mine          Enable mining mode
--validate      Run validator node
--rpc           Enable RPC server (default: true)
```

#### Access the RPC endpoint:
```bash
http://localhost:8545
```

## 📊 Monitoring Dashboard
### Run monitoring stack with Docker:

```bash
cd deploy
docker-compose up -d
```
Access Grafana at:
```bash
http://localhost:3000
Default credentials:

pgsql
Copy code
User: admin
Password: admin

```

## 🪙 Tokenomics (Zyth Coin)
- Parameter	Description
- Token Name	: Zyth
- Symbol	: ZYTH
- Consensus	: PoW + PoS Hybrid
- Block Reward	: 3 ZYTH
- Max Supply :	21,000,000 ZYTH
- Staking Reward :	Dynamic (AI-optimized)

## 🧠 Future Roadmap
 - Core PoW engine in Rust
 - Go-based node with P2P networking
 - Grafana integration for monitoring
 - AI validator with TensorFlow
 - Smart contract SDK (WASM runtime)
 - Testnet launch

## 🧑‍💻 Contributors
- @zhao-leihan — Lead Developer, Architect, Blockchain Developer, Backend Developer
- @BabyGracia - Support System

------------------------------------------------------------------------------------------------------------------------------------------------------------------------

