use ring::{
    rand::SystemRandom,
    signature::{Ed25519KeyPair, KeyPair as _, UnparsedPublicKey, ED25519},
};
use sha2::{Sha256, Digest};
use std::fmt;

#[derive(Debug)]
pub struct KeyPair {
    inner: Ed25519KeyPair,
}

impl KeyPair {
    pub fn generate() -> Self {
        let rng = SystemRandom::new();
        let pkcs8 = Ed25519KeyPair::generate_pkcs8(&rng)
            .expect("Failed to generate Ed25519 keypair");
        let keypair = Ed25519KeyPair::from_pkcs8(pkcs8.as_ref())
            .expect("Failed to parse keypair");
        Self { inner: keypair }
    }

    pub fn from_seed(seed: &[u8]) -> Result<Self, Box<dyn std::error::Error>> {
        // Ed25519 seed must be 32 bytes
        if seed.len() != 32 {
            return Err("Seed must be 32 bytes".into());
        }
        let keypair = Ed25519KeyPair::from_seed_unchecked(seed)
            .map_err(|e| format!("Key generation failed: {:?}", e))?;
        Ok(Self { inner: keypair })
    }

    pub fn public_key(&self) -> Vec<u8> {
        self.inner.public_key().as_ref().to_vec()
    }

    pub fn sign(&self, message: &[u8]) -> Vec<u8> {
        self.inner.sign(message).as_ref().to_vec() // 64 bytes
    }
}

pub fn verify_signature(public_key: &[u8], message: &[u8], signature: &[u8]) -> bool {
    let public_key = UnparsedPublicKey::new(&ED25519, public_key);
    public_key.verify(message, signature).is_ok()
}

pub fn hash_data(data: &[u8]) -> String {
    let mut hasher = Sha256::new();
    hasher.update(data);
    format!("{:x}", hasher.finalize())
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize, PartialEq, Eq, Hash)]
pub struct Address(String);

impl Address {
    pub fn from_public_key(public_key: &[u8]) -> Self {
        let hash = hash_data(public_key);
        Self(format!("ZYTH_{}", &hash[..40]))
    }

    pub fn as_str(&self) -> &str {
        &self.0
    }

    pub fn from_string(s: String) -> Self {
        Self(s)
    }
}

impl fmt::Display for Address {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.0)
    }
}

// Clone is auto-derived if all fields support it
#[derive(Debug, Clone)]
pub struct ClonableKeyPair {
    pub public_key: Vec<u8>,
    // Note: Ed25519KeyPair doesn't implement Clone, so we don't store it directly if you need Clone
    // But for most uses, you don't need to clone the private key
}