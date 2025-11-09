@echo off
echo === Zytherion Build and Test ===

:: Check prerequisites
echo Checking prerequisites...

where cargo >nul 2>nul
if %errorlevel% equ 0 (
    echo ✓ Rust/Cargo found
) else (
    echo ✗ Rust/Cargo not found. Please install Rust from https://rustup.rs/
    exit /b 1
)

where go >nul 2>nul
if %errorlevel% equ 0 (
    echo ✓ Go found
) else (
    echo ⚠ Go not found. Go node will not be built.
)

where python >nul 2>nul
if %errorlevel% equ 0 (
    echo ✓ Python found
) else (
    echo ⚠ Python not found. AI validator will not be built.
)

:: Build Rust core
echo.
echo Building Rust core...
cd core

echo Running cargo check...
cargo check
if %errorlevel% equ 0 (
    echo ✓ Rust core compiles successfully
) else (
    echo ✗ Rust core compilation failed
    exit /b 1
)

echo Running cargo build...
cargo build
if %errorlevel% equ 0 (
    echo ✓ Rust core built successfully
) else (
    echo ✗ Rust core build failed
    exit /b 1
)

echo Running unit tests...
cargo test
if %errorlevel% equ 0 (
    echo ✓ All unit tests passed
) else (
    echo ✗ Unit tests failed
    exit /b 1
)

cd ..

:: Build Go node (if Go is available)
where go >nul 2>nul
if %errorlevel% equ 0 (
    echo.
    echo Building Go node...
    cd node
    
    echo Running go mod tidy...
    go mod tidy
    
    echo Running go build...
    go build -o zytherion-node.exe
    if %errorlevel% equ 0 (
        echo ✓ Go node built successfully
    ) else (
        echo ✗ Go node build failed
    )
    
    cd ..
) else (
    echo ⚠ Skipping Go node build (Go not installed)
)

:: Run the demo
echo.
echo Running Rust core demo...
cd core
cargo run --bin zytherion-core
if %errorlevel% equ 0 (
    echo ✓ Demo completed successfully
) else (
    echo ✗ Demo failed
    exit /b 1
)
cd ..

echo.
echo === All builds completed successfully! ===
echo.
echo Next steps:
echo 1. Run 'core\target\debug\zytherion-core.exe' for Rust demo
echo 2. Run 'node\zytherion-node.exe start' for Go node (if built)
echo 3. Run 'cd ai_validator && python server.py' for AI validator
echo.
echo Project structure overview:
echo • core\     - Rust implementation (consensus, crypto, contracts)
echo • node\     - Go implementation (networking, RPC, CLI)
echo • ai_validator\ - Python implementation (machine learning)
echo.
echo For more information, see README.md