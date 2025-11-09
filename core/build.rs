fn main() {
    // Build script for zytherion-core
    println!("cargo:rerun-if-changed=src/");
    
    // Add build-time configuration
    println!("cargo:rustc-cfg=feature=\"ai_validation\"");
}