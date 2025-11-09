use zytherion_core::*;


fn main() {
    println!("=== Zytherion Core Demo ===");
    
    // 1. Generate cryptographic keys
    println!("\n1. Generating cryptographic keys...");
    let keypair = crypto::KeyPair::generate();
    let address = crypto::Address::from_public_key(&keypair.public_key());
    println!("   Address: {}", address);
    println!("   Public key: {}", hex::encode(&keypair.public_key()));

    // 2. Create a sample transaction
    println!("\n2. Creating sample transaction...");
    let tx = block::Transaction {
        from: address.clone(),
        to: crypto::Address::from_string("ZYTH_RECIPIENT_1234567890".to_string()),
        amount: 1000,
        fee: 10,
        nonce: 0,
        signature: vec![],
        timestamp: chrono::Utc::now().timestamp() as u64,
        data: None,
    };
    println!("   Transaction: {} ZYTH from {} to {}", 
             tx.amount, tx.from, tx.to);

    // 3. Create a block
    println!("\n3. Creating genesis block...");
    let block = block::Block::new(
        "0x0000000000000000000000000000000000000000000000000000000000000000".to_string(),
        vec![tx],
        1,
        0,
    );
    println!("   Block hash: {}", block.hash);
    println!("   Block height: {}", block.header.height);
    println!("   Transactions in block: {}", block.transactions.len());

    // 4. Demonstrate PoW mining
    println!("\n4. Demonstrating Proof of Work...");
    let pow = pow::ProofOfWork::new(2); // Low difficulty for demo
    if let Some(mined_block) = pow.mine_block(block) {
        println!("   Successfully mined block!");
        println!("   Final nonce: {}", mined_block.header.nonce);
        println!("   Final hash: {}", mined_block.hash);
    }

    // 5. Demonstrate PoS staking
    println!("\n5. Demonstrating Proof of Stake...");
    let mut pos = pos::ProofOfStake::new(1000, 259200);
    let staker_address = crypto::Address::from_string("ZYTH_STAKER_1234567890".to_string());
    pos.add_staker(staker_address.clone(), 5000, chrono::Utc::now().timestamp() as u64);
    println!("   Added staker with 5000 ZYTH");
    println!("   Total stake: {} ZYTH", pos.total_stake);
    println!("   Stakers count: {}", pos.stakers.len());

    // 6. Demonstrate contract engine
    println!("\n6. Demonstrating Smart Contract Engine...");
    let mut contract_engine = contract_engine::ContractEngine::new();
    let token_contract = contract_engine::templates::create_token_template(
        address.clone(),
        1000000,
    );
    let contract_id = contract_engine.deploy_contract(token_contract).unwrap();
    println!("   Deployed contract: {}", contract_id);

    // 7. Demonstrate state management
    println!("\n7. Demonstrating State Management...");
    let mut state = state::State::new();
    let account = state::Account {
        address: address.clone(),
        balance: 10000,
        nonce: 0,
        staked_amount: 5000,
        is_validator: true,
    };
    state.update_account(account);
    println!("   Created account with balance: 10000 ZYTH");
    println!("   Total supply: {} ZYTH", state.get_total_supply());

    println!("\n=== Demo Completed Successfully! ===");
    println!("\nNext steps:");
    println!("1. Run 'cargo test' to run unit tests");
    println!("2. Build the Go node for full network functionality");
    println!("3. Start the AI validator service");
}